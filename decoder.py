import numpy as np

e = "temp.c,3 humidity,2 co2.ppm,2 voc.ppm,1"
d = "Manifold_hot:20.2224 Manifold_cold1:18.1245 Manifold_cold2:17.1234 5':83 10':72 5':221 10':268 voc:50"


def one_fell_swoop(e, d):
    # Split the event and data from Particle SSEClient
    key = e.split()
    _values = d.split()

    # Return's results of a split as two np.array columns
    def split_col(input_column, delim, return_one_array=False):
        # these will hold our lists
        col_1 = []
        col_2 = []

        for i in input_column:
            _s = i.split(delim)

            # add events
            try:
                col_1.append(_s[0])
            except:
                col_1.append("error")

            # add units (if possible)
            try:
                col_2.append(_s[1])
            except:
                col_2.append("None")

        col_1 = np.array(col_1).reshape([len(col_1), 1])
        col_2 = np.array(col_2).reshape([len(col_2), 1])

        if return_one_array:
            return append_cols(col_1, col_2, 0)
        else:
            return col_1, col_2

    # create a row for each value received
    def interpret_values(key, values):
        z = np.array(values, dtype="a128").reshape([len(values), 1])
        z = np.append(z, np.array(split_col(z, 0, ":")).reshape([len(z), 1]), axis=1)
        z[:, 0] = np.array(split_col(z, 0, ":", 0))
        return z

    # Append two columns
    def append_cols(a, b, axis=1):
        if a.shape != (len(_values), 1):
            a.reshape([len(a), 1])
        b.reshape([len(b), 1])
        return np.append(a, b, 1)

    # Expand Key
    def expand_keys(key_arr):
        new_arr = np.empty([0, key_arr.shape[1]])
        for counter, r in enumerate(key_arr):
            new_arr = np.append(new_arr, np.repeat([key_arr[counter]], int(r[1]), axis=0), axis=0)
        return new_arr

    # Returns cleaned EVENT column, UNIT column
    def parse_events(key, return_one_array=False):
        _s = split_col(key, ',')

        # these will hold our lists
        events = np.array(_s[0]).reshape([len(key), 1])
        units = np.array(_s[1]).reshape([len(key), 1])

        if return_one_array:
            return append_cols(events, units, 0)
        else:
            return events, units

    # Move units if one exists
    def correct_units(events):
        return split_col(events[:, 0], ".", True)

    split_values = split_col(_values, ":")
    labels = split_values[0].reshape([len(_values), 1])
    data = split_values[1].reshape([len(_values), 1])
    events = expand_keys(parse_events(key, True))
    events = correct_units(events)

    complete_arr = np.append(labels, data, 1)
    complete_arr = np.append(complete_arr, events, 1)

    return complete_arr

# print one_fell_swoop(e, d)

