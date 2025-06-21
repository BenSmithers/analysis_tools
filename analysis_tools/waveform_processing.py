import numpy as np

class WaveformProcessing:
    def __init__(self):
        self.cfd_raw_t = [0.16323452713658082,
                        0.20385733509493395,
                        0.24339187740767365,
                        0.2822514122310461,
                        0.3208335490313887,
                        0.35953379168152044,
                        0.3987592183841288,
                        0.4389432980060811,
                        0.4805630068163285,
                        0.5241597383052767,
                        0.5703660640730557,
                        0.6199413381955754,
                        0.6738206794685682,
                        0.7331844507933303,
                        0.7995598000823612,
                        0.874973724581176,
                        0.9621917102137131,
                        1.0301530251726216,
                        1.0769047405430523,
                        1.1210801763323819,
                        1.1632345271365807]

        # correction for the amplitude derived by summing the largest three adcs
        self.amp_raw_t = [2.0413475167493225, 2.0642014124776784, 2.0847238089021274, 2.1028869067818117, 2.118667914530039,
                    2.1320484585033723, 2.1430140317025583, 2.151553497195665, 2.1576586607668613, 2.1613239251470255,
                    2.162546035746829, 2.1613239251470255, 2.1576586607668617, 2.1515534971956654, 2.143014031702558,
                    2.1320484585033723, 2.118667914530039, 2.1028869067818117, 2.0847238089021274, 2.0642014124776784,
                    2.0413475167493225]

        self.cfd_true_t = [-0.5 + 0.05*i for i in range(21)]

    def get_peak_timebins(self,waveform, threshold):
        # the following is from process_root
        # note that the waveforms in the parquet file are already baseline subtracted and inverted
        # So reverse the sign of baseline and adcs in the get_cfd function
        # use the most frequent waveform value as the baseline
        values, counts = np.unique(waveform, return_counts=True)
        baseline = values[np.argmax(counts)]
        # baseline - waveform is positive going signal typically around 0 when there is no signal
        # threshold is the minimum positive signal above baseline

        below = (waveform[0] - baseline) <= threshold
        peak_timebins = []
        max_val = 0
        max_timebin = -1
        for i in range(len(waveform)):
            if below and (waveform[i] - baseline) > threshold:
                below = False
                max_val = 0
                max_timebin = -1
            if not below:
                if (waveform[i] - baseline) > max_val:
                    max_val = waveform[i] - baseline
                    max_timebin = i
                if (waveform[i] - baseline) <= threshold:
                    below = True
                    #if brb != 3 or len(peak_timebins) == 0 or max_timebin > peak_timebins[-1] + 4:  # eliminate peaks from ringing... (for brb03)
                    if 1 == 1:
                        peak_timebins.append(max_timebin)
        return peak_timebins

    def cfd_teststand_method(self, adcs):
        #taken from the process_parquet test stand method
        # Use a cfd like algorithm with delay d = 2, multiplier c = -2
        c = -2.
        d = 2
        # for cfd just use the average of the first 3 adcs as the baseline
        baseline = (adcs[0] + adcs[1] + adcs[2]) / 3.
        # the amplitude is found by adding the highest 3 adcs and subtracting the baseline
        #amp = (baseline - np.min(adcs)) / 100.
        n_largest_vals = sorted(np.array(adcs)-baseline, reverse=True)[:3]
        amp = sum(n_largest_vals)
        # converting to positive going pulses
        data = [(adcs[i]-baseline) + c * (adcs[i - d]-baseline) for i in range(d, len(adcs))]
        # find largest swing zero crossing
        max_diff = 0
        i_md = -1
        for iv in range(1, len(data)):
            if data[iv - 1] > 0. and data[iv] < 0.:
                if data[iv - 1] - data[iv] > max_diff:
                    max_diff = data[iv - 1] - data[iv]
                    i_md = iv

        if i_md > -1:
            x0 = i_md - 1
            y0 = data[i_md - 1]
            x1 = i_md
            y1 = data[i_md]

            # using a linear interpolation, find the value of x for which y = 0
            x = x0 - (x1 - x0) / (y1 - y0) * y0
            # apply offset assuming sigma = 0.96 (see try_cfd.ipynb)
            #x -= 0.5703
            # apply a correction
            apply_correction = True
            offset = 5.
            delta = x - offset
            t = None
            if apply_correction:
                if self.cfd_raw_t[0] < delta < self.cfd_raw_t[-1]:
                    correct_t = np.interp(delta,self.cfd_raw_t,self.cfd_true_t)
                    t = offset + correct_t
                elif delta < self.cfd_raw_t[0]:
                    delta += 1
                    if self.cfd_raw_t[0] < delta < self.cfd_raw_t[-1]:
                        correct_t = np.interp(delta, self.cfd_raw_t, self.cfd_true_t)
                        t = offset - 1 + correct_t
                elif delta > self.cfd_raw_t[-1]:
                    delta -= 1
                    if self.cfd_raw_t[0] < delta < self.cfd_raw_t[-1]:
                        correct_t = np.interp(delta, self.cfd_raw_t, self.cfd_true_t)
                        t = offset + 1 + correct_t
            if t is None:
                t = x - 0.5703
                amp = amp/2.118 # average correction
            else:
                correct_amp = np.interp(correct_t, self.cfd_true_t, self.amp_raw_t)
                amp /= correct_amp

        else:
            t = -999
            amp = -999

        return t, amp, baseline

