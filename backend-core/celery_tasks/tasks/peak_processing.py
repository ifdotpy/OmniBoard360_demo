import pandas as pd

from celery_tasks.celery import app
from celery_tasks.hplc_processing import HPLCProcessing
from siebox.consumer.channel_layer import ChannelUtils
from siebox.model.measurement import Measurement
from siebox.model.peak import Peak as PeakModel


@app.task()
def send_measurement(_, channel, injection_id):
    if channel is not None and injection_id is not None:
        channel_utils_method = getattr(ChannelUtils, channel)
        if channel_utils_method is not None:
            channel_utils_method(injection_id)


@app.task()
def add_peak(measurement_id: int, start: dict, end: dict):
    m = Measurement.objects.get(pk=measurement_id)

    data = m.get_data_series().loc[start['time']:end['time']]

    peak = HPLCProcessing.calc_raw_peak(data, start, end)

    peak_model = PeakModel.create(m, peak.start, peak.apex, peak.end, peak.area, peak.start_mau, peak.end_mau)
    peak_model.save()


@app.task()
def manual_baseline(measurement_id: int, points):
    # print('Started')
    # print(points)
    m = Measurement.objects.get(pk=measurement_id)

    baseline = {point['time']: point['mau'] for point in points}
    baseline = pd.Series(baseline)

    # print(baseline)

    period = m.period
    y = m.get_data_intarray()
    x = [(i * period) / 1000 / 60 for i in range(len(y))]

    baseline = baseline.reindex(x, tolerance=x[1] - x[0], method='nearest').interpolate(limit_direction='both')

    # print(baseline)
    m.set_baseline(baseline)


@app.task()
def find_baseline(measurement_id):
    print('Started')
    m = Measurement.objects.get(pk=measurement_id)
    m.start_processing()
    try:
        period = m.period
        y = m.get_data_intarray()
        x = [(i * period) / 1000 / 60 for i in range(len(y))]
        data = pd.Series(y, index=x)
        baseline = HPLCProcessing(data).process_baseline()
        print(f'Baseline: {baseline}')

        m.set_baseline(baseline)
    finally:
        m.finish_processing()


@app.task()
def process_peaks(measurement_id):
    print('Started', flush=True)
    m = Measurement.objects.get(pk=measurement_id)
    m.start_processing()
    try:
        period = m.period
        print('period ' + str(period), flush=True)
        y = m.get_data_intarray()
        print(f'{y}', flush=True)
        x = [(i * period) / 1000 / 60 for i in range(len(y))]
        data = pd.Series(y, index=x)
        processing = HPLCProcessing(data)
        peaks, baseline = processing.process()
        print(f'Peaks count: {len(peaks)}', flush=True)
        print(f'Baseline: {baseline}', flush=True)

        m.set_baseline(baseline)

        PeakModel.clear_for_measurement(m)

        print('cleared', flush=True)

        for peak in peaks:
            peak_model = PeakModel.create(m, peak.start, peak.apex, peak.end, peak.area)
            peak_model.save()
            if peak.is_mixed_peak:
                pass
                # for subpeak in peak.peaks:
                #     subpeak_model = PeakModel.create(m, subpeak.start, subpeak.apex, subpeak.end, subpeak.area,
                #                                      peak_model.id)
                #     subpeak_model.save()

        for i, peak in enumerate(peaks):
            print(f'- Peak N {i}')
            print(f'  Bounds: [{peak.start}, {peak.end}]')
            print(f'  Center index: {peak.apex}')
            print(f'  Area: {peak.area}')
            if peak.is_mixed_peak:
                print(f'  Baseline: {peak.baseline}')
                print(f'  Params: {peak.gaussian_params}')
                for j, subpeak in enumerate(peak.peaks):
                    print(f'  - Subpeak N {j}')
                    print(f'    Bounds: [{subpeak.start}, {subpeak.end}]')
                    print(f'    Center index: {subpeak.apex}')
                    print(f'    Baseline: {subpeak.baseline}')
                    print(f'    Area: {subpeak.area}')
                    print(f'    Params: {subpeak.gaussian_params}')
    finally:
        m.finish_processing()
