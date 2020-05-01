from numba import int32, float64,boolean, int64, prange, njit, types
import numpy as np

numba_model_spec = [
    ('eq_count', int32),
    ('number_of_states', int32),
    ('number_of_mappings', int32),
    ('scope_vars_3d', float64[:, :, :]),
    ('state_idxs_3d', types.Tuple((int64[:], int64[:], int64[:]))),
    ('deriv_idxs_3d', types.Tuple((int64[:], int64[:], int64[:]))),
    ('differing_idxs_pos_3d', types.Tuple((int64[:], int64[:], int64[:]))),
    ('differing_idxs_from_3d', types.Tuple((int64[:], int64[:], int64[:]))),
    ('num_uses_per_eq', int64[:]),
    ('sum_idxs_pos_3d', types.Tuple((int64[:], int64[:], int64[:]))),
    ('sum_idxs_sum_3d', types.Tuple((int64[:], int64[:], int64[:]))),
    ('sum_slice_idxs', int64[:,:]),
    ('sum_mapping', boolean),
    ('global_vars', float64[:]),
]


class NumbaModel:
    def __init__(self, eq_count, number_of_states, number_of_mappings, scope_vars_3d, state_idxs_3d, deriv_idxs_3d,
                 differing_idxs_pos_3d, differing_idxs_from_3d,num_uses_per_eq,
                 sum_idxs_pos_3d,sum_idxs_sum_3d,sum_slice_idxs,sum_mapping,
                 global_vars):
        self.eq_count = eq_count
        self.number_of_states = number_of_states
        self.scope_vars_3d = scope_vars_3d
        self.state_idxs_3d = state_idxs_3d
        self.deriv_idxs_3d = deriv_idxs_3d
        self.differing_idxs_pos_3d = differing_idxs_pos_3d
        self.differing_idxs_from_3d = differing_idxs_from_3d
        self.num_uses_per_eq = num_uses_per_eq
        self.number_of_mappings = number_of_mappings
        self.sum_idxs_pos_3d = sum_idxs_pos_3d
        self.sum_idxs_sum_3d = sum_idxs_sum_3d
        self.sum_slice_idxs = sum_slice_idxs
        self.sum_mapping = sum_mapping
        self.global_vars = global_vars


    def update_states(self, state_values):
        for i in range(self.number_of_states):
            self.scope_vars_3d[self.state_idxs_3d[0][i]][self.state_idxs_3d[1][i]][self.state_idxs_3d[2][i]]\
                = state_values[i]


    def update_states_idx(self, state_value, idx_3d):
        self.scope_vars_3d[idx_3d] = state_value

    def get_derivatives(self):
        result = []
        for i in range(self.number_of_states):
            result.append(self.scope_vars_3d[self.deriv_idxs_3d[0][i]][self.deriv_idxs_3d[1][i]][self.deriv_idxs_3d[2][i]])
        return result
    def get_derivatives_idx(self, idx_3d):
        return self.scope_vars_3d[idx_3d]

    def compute(self):
        if self.sum_mapping:
            sum_mappings(self.sum_idxs_pos_3d, self.sum_idxs_sum_3d,
                         self.sum_slice_idxs, self.scope_vars_3d)

        mapping_ = True
        prev_scope_vars_3d = self.scope_vars_3d.copy()
        while mapping_:
            for i in range(self.number_of_mappings):
                self.scope_vars_3d[self.differing_idxs_pos_3d[0][i]][self.differing_idxs_pos_3d[1][i]][self.differing_idxs_pos_3d[2][i]] = self.scope_vars_3d[
                    self.differing_idxs_from_3d[0][i]][self.differing_idxs_from_3d[1][i]][self.differing_idxs_from_3d[2][i]]
            self.compute_eq(self.scope_vars_3d)

            if self.sum_mapping:
                sum_mappings(self.sum_idxs_pos_3d, self.sum_idxs_sum_3d,
                             self.sum_slice_idxs, self.scope_vars_3d)

            mapping_ = not np.all(np.abs(prev_scope_vars_3d - self.scope_vars_3d) < 1e-6)
            prev_scope_vars_3d = np.copy(self.scope_vars_3d)

    def func(self, _t, y):
        # self.info["Number of Equation Calls"] += 1
        self.update_states(y)
        self.global_vars[0] = _t
        self.compute()

        return self.get_derivatives()


@njit
def sum_mappings(sum_idxs_pos_3d, sum_idxs_sum_3d,
                 sum_slice_idxs, scope_vars_3d):
    for i in range(sum_slice_idxs.shape[0]):
        scope_vars_3d[sum_idxs_pos_3d[0][i]][sum_idxs_pos_3d[1][i]][sum_idxs_pos_3d[2][i]] = 0
        for j in sum_slice_idxs[i]:
            scope_vars_3d[sum_idxs_pos_3d[0][i]][sum_idxs_pos_3d[1][i]][sum_idxs_pos_3d[2][i]] \
                += scope_vars_3d[sum_idxs_sum_3d[0][j]][sum_idxs_sum_3d[1][j]][sum_idxs_sum_3d[2][j]]