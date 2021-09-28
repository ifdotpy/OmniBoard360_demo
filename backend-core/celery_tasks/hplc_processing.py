import itertools

from scipy import signal, sparse, stats, optimize
from scipy.sparse import linalg
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Any

QUANTILE_MAX_DIFF = 0.3
MIN_SECONDS_PER_PEAK = 5


def _1skew_gaussian(x, h, a, b, c):
    return h * stats.skewnorm.pdf(x, -a, b, c)


class Peak:
    def __init__(self, apex, start=None, end=None, start_mau=None, end_mau=None):
        self.apex = apex  # extreamum in minutes

        self.start = start  # left right bounds in minutes
        self.end = end

        self.start_mau = start_mau  # left right bounds in mau
        self.end_mau = end_mau

        self.peaks: List[Peak] = []  # child peaks

        # for mixed peaks
        self.gaussian_params = None
        self.baseline = None  # mAU height digit
        # final params
        self.area = None

    @property
    def is_mixed_peak(self):
        return len(self.peaks) > 0

    @property
    def is_manual_peak(self):
        return self.start_mau is not None and self.end_mau is not None

    def get_data_slice(self, data: pd.Series) -> pd.Series:  # slice data for peak
        return data.loc[self.start:self.end]


class HPLCProcessing:
    def __init__(self, data: pd.Series):
        self.data = data  # raw values {min: mAU}
        self.corrected_data = None
        self.baseline = None

    # Main pipeline
    # threshold - min peak height
    def process(self) -> Tuple[List[Peak], Any]:
        data: pd.Series = self.data.copy()

        data = self.preprocess(data)

        data, self.baseline = self.correct_baseline(data)
        self.corrected_data = data

        threshold = self.find_threshold(data)
        # find only extremum
        peak_indices = self.find_peaks(data, threshold)

        # positions in series of starts and ends peaks
        widths_sizes, widths_starts, widths_ends = self.define_peak_widths(data, peak_indices)

        peak_indices, widths_sizes, widths_starts, widths_ends = \
            self.filter_peaks(data, peak_indices, widths_sizes, widths_starts, widths_ends)

        peaks = self.create_peaks(data, peak_indices, widths_starts, widths_ends)

        peaks = self.fold_peaks(peaks)

        peaks = self.fit_peaks(data, peaks)

        peaks = self.set_area_peaks(data, peaks)

        return peaks, self.baseline

    def process_baseline(self):
        data: pd.Series = self.data.copy()
        data = self.preprocess(data)
        return self.get_baseline(data)

    @classmethod
    def calc_raw_peak(cls, data: pd.Series, start: dict, end: dict) -> Peak:
        data: pd.Series = data.copy()

        apex_ind = cls.find_peak(data)

        peak = cls.create_peak(data, apex_ind, start['time'], end['time'], start['mau'], end['mau'])

        peak = cls.set_area_peak(data, peak)

        return peak

    ###############

    @classmethod
    def find_peaks(cls, data: pd.Series, threshold: float) -> np.ndarray:
        mps = cls._get_mps(data)
        distance = mps * MIN_SECONDS_PER_PEAK
        peaks_indices, _ = signal.find_peaks(data, height=threshold, distance=distance)
        return peaks_indices

    @classmethod
    def find_peak(cls, data: pd.Series) -> int:
        return data.values.argmax()

    @classmethod
    def create_peak(cls, data, apex_ind, l_bound, r_bound, l_bound_mau=None, r_bound_mau=None) -> Peak:
        apex = data.index[apex_ind]
        return Peak(apex, l_bound, r_bound, l_bound_mau, r_bound_mau)

    @classmethod
    def create_peaks(cls, data: pd.Series, peak_indices: np.ndarray, widths_starts: pd.Series,
                     widths_ends: pd.Series) -> List[Peak]:
        peaks_count = len(peak_indices)
        peaks: List[Peak] = []
        for i in range(peaks_count):
            apex_ind = peak_indices[i]
            l_bound = widths_starts.index[i]
            r_bound = widths_ends.index[i]

            peak = cls.create_peak(data, apex_ind, l_bound, r_bound)
            peaks.append(peak)
        return peaks

    # todo: need optimizations, not effective algorithm
    @classmethod
    def fold_peaks(cls, peaks: List[Peak]) -> List[Peak]:
        # sorted_peaks = sorted(peaks, key=lambda o: o.r_bound - o.l_bound)
        # todo: fold peaks like [1, 3] [2, 4]
        for peak in peaks:
            peak.peaks = list(filter(lambda o: o.start > peak.start and o.end < peak.end, peaks))
            peak.peaks = sorted(peak.peaks, key=lambda o: o.apex)

        all_folded_peaks = list(itertools.chain.from_iterable([peak.peaks for peak in peaks]))

        peaks = list(filter(lambda o: o not in all_folded_peaks, peaks))

        # for peak in peaks:
        #     peak.peaks = list(filter(lambda o: peak.start < o.start < peak.end < o.end, peaks))
        #     peak.peaks = sorted(peak.peaks, key=lambda o: o.apex_ind)
        #
        # all_mixed_peaks = list(itertools.chain.from_iterable([peak.peaks for peak in peaks]))
        #
        # peaks = list(filter(lambda o: o not in all_mixed_peaks, peaks))

        return peaks

    @classmethod
    def fit_peaks(cls, data: pd.Series, peaks: List[Peak]) -> List[Peak]:
        for peak in peaks:
            if peak.is_mixed_peak:
                data_slice = peak.get_data_slice(data)

                initial_p = cls.get_fit_func_params(data, peak)
                curve_func = cls.gen_fit_func(len(peak.peaks) + 1)

                # todo: check fail in fitting
                params, _ = optimize.curve_fit(curve_func, data_slice.index, data_slice, p0=initial_p)

                peak.baseline, params = params[0], params[1:]
                peak.gaussian_params, params = params[:4], params[4:]

                for i, inner_peak in enumerate(peak.peaks):
                    start_i = i * 4
                    inner_peak.baseline = peak.baseline
                    inner_peak.gaussian_params = params[start_i:start_i + 4]

        return peaks

    @classmethod
    def filter_peaks(cls, data, peak_indices, widths_sizes, widths_starts, widths_ends):
        mps = cls._get_mps(data)
        filter = widths_sizes > (mps * MIN_SECONDS_PER_PEAK)

        peak_indices = peak_indices[filter]
        widths_sizes = widths_sizes[filter]
        widths_starts = widths_starts[filter]
        widths_ends = widths_ends[filter]

        return peak_indices, widths_sizes, widths_starts, widths_ends

    @classmethod
    def set_area_peak(cls, data, peak):
        if peak.is_mixed_peak:
            peak.area = cls._area_mixed_peak(data, peak)
            for inner_peak in peak.peaks:
                inner_peak.area = cls._area_mixed_peak(data, inner_peak)
        elif peak.is_manual_peak:
            peak.area = cls.area_manual_peak(data, peak)
        else:
            data_slice = peak.get_data_slice(data)
            data_slice -= cls.baseline_lin(data_slice)
            peak.area = cls.area_peak(data_slice)
        return peak

    @classmethod
    def set_area_peaks(cls, data: pd.Series, peaks: List[Peak]) -> List[Peak]:
        for peak in peaks:
            cls.set_area_peak(data, peak)
        return peaks

    @classmethod
    def _area_mixed_peak(cls, data: pd.Series, peak: Peak) -> float:
        return peak.gaussian_params[0]

    @classmethod
    def area_manual_peak(cls, data: pd.Series, peak: Peak) -> float:
        trapezoid_area = (peak.end - peak.start) * (peak.start_mau + peak.end_mau) / 2
        peak_area = cls.area_peak(data)
        return peak_area - trapezoid_area

    @classmethod
    def area_peak(cls, data: pd.Series) -> float:
        return np.trapz(data, data.index)

    @classmethod
    def define_peak_widths(cls, data: pd.Series, peak_indices: np.ndarray) -> Tuple[np.ndarray, pd.Series, pd.Series]:
        ind_widths = signal.peak_widths(data, peak_indices, rel_height=0.99)

        widths_sizes, widths_starts, widths_ends = ind_widths[0], data.iloc[ind_widths[2]], data.iloc[ind_widths[3]]

        return widths_sizes, widths_starts, widths_ends

    @classmethod
    def _get_mps(cls, data: pd.Series) -> float:
        last_x = data.index.values[-1]  # Last value of a time
        return (len(data) - 1) / last_x / 60

    @classmethod
    def _absolute_values(cls, data: pd.Series) -> pd.Series:
        return data.abs()

    @classmethod
    def preprocess(cls, data: pd.Series) -> pd.Series:
        median = data.median()
        # print(f'median {median}')
        if median < 0:
            median = abs(median)
            data = data.apply(lambda o: o + median)
        data = cls._absolute_values(data)
        return data

    @classmethod
    def downscale_data(cls, data: pd.Series) -> pd.Series:
        MPS_GOAL = 0.5
        mps = cls._get_mps(data)
        # print(f'mps {mps}')
        scale = int(np.round(mps / MPS_GOAL))
        # print(f'scale {scale}')
        return data.iloc[::scale]

    @classmethod
    def find_threshold(cls, data: pd.Series) -> float:
        lsp = np.linspace(0.5, 1, 100)
        quantiles = pd.Series([(np.quantile(data, i)) for i in lsp], index=lsp)
        quantiles_diffs = quantiles.values[1:] - quantiles.values[:-1]
        index = np.argmax(quantiles_diffs > QUANTILE_MAX_DIFF)
        return quantiles.iloc[index]

    @classmethod
    def baseline_als(cls, y: np.ndarray, lam, p, niter) -> np.ndarray:
        assert (niter > 0)
        length = len(y)
        D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(length, length - 2))
        D = lam * D.dot(D.transpose())
        w = np.ones(length)
        W = sparse.spdiags(w, 0, length, length)
        z: np.ndarray = None
        for i in range(niter):
            W.setdiag(w)
            Z = W + D
            z: np.ndarray = linalg.spsolve(Z, w * y)
            w = p * (y > z) + (1 - p) * (y < z)
        return z

    @classmethod
    def baseline_lin(cls, data: pd.Series):
        length = len(data)
        first_val = data.iloc[0]
        last_val = data.iloc[-1]
        return np.linspace(first_val, last_val, length, endpoint=True)

    @classmethod
    def get_baseline(cls, data: pd.Series) -> pd.Series:
        # Prepared constant for MPS == 0.5
        LAM = 167
        d_data = cls.downscale_data(data)
        result = cls.baseline_als(d_data.to_numpy(), LAM, 0, 10)
        result = pd.Series(result, index=d_data.index)
        result = result.reindex(data.index).interpolate('index')
        return result

    @classmethod
    def correct_baseline(cls, data: pd.Series) -> pd.Series:
        baseline = cls.get_baseline(data)
        baseline = pd.concat([data, baseline], axis=1).min(axis=1)
        result = data - baseline
        return result, baseline

    @classmethod
    def correct_baseline_manual(cls, data: pd.Series, start: dict, end: dict) -> pd.Series:
        return data

    ################
    @classmethod
    def _get_fit_func_param(cls, data: pd.Series, peak: Peak):
        height = data.loc[peak.apex]
        center = peak.apex

        return [height / 10, 1, center, 0.1]

    @classmethod
    def get_fit_func_params(cls, data: pd.Series, peak: Peak) -> List[float]:
        peak_data_slice = peak.get_data_slice(data)
        sub_peaks = (cls._get_fit_func_param(data, sub_peak) for sub_peak in peak.peaks)
        return [peak_data_slice.min()] + cls._get_fit_func_param(data, peak) + list(
            itertools.chain.from_iterable(sub_peaks))

    @classmethod
    def gen_fit_func(cls, peaks_count: int):
        def fit_func(x, baseline, *args):
            assert len(args) == peaks_count * 4
            return sum((_1skew_gaussian(x, *args[i:i + 4]) for i in range(0, peaks_count * 4, 4))) + baseline

        return fit_func
