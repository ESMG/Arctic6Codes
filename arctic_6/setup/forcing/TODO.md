# TODO

This file constains a list of tasks for improving
the `forcing` code:

## Out of memory

 - The forcing code currently exhibits a memory leak.
   The program will stop working after processing of
   about 20 fields (< 2 years).

```
ERA5_2m_specific_humidity
-> 1993
  -> subset
  -> make_periodic
  -> era_cut
  -> flood
-> 1994
  -> subset
Traceback (most recent call last):
  File "subset_calc_era5.py", line 476, in <module>
    smr = saturation_mixing_ratio(pair, tdew)
  File "subset_calc_era5.py", line 59, in saturation_mixing_ratio
    return mixing_ratio(saturation_vapor_pressure(temperature), total_press)
  File "subset_calc_era5.py", line 45, in mixing_ratio
    / (total_press - partial_press))
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/_typed_ops.py", line 209, in __sub__
    return self._binary_op(other, operator.sub)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/dataarray.py", line 3021, in _binary_op
    if not reflexive
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/_typed_ops.py", line 399, in __sub__
    return self._binary_op(other, operator.sub)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/variable.py", line 2330, in _binary_op
    self_data, other_data, dims = _broadcast_compat_data(self, other)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/variable.py", line 2799, in _broadcast_compat_data
    self_data = new_self.data
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/variable.py", line 347, in data
    return self.values
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/variable.py", line 520, in values
    return _as_array_or_item(self._data)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/variable.py", line 262, in _as_array_or_item
    data = data.get() if isinstance(data, cupy_array_type) else np.asarray(data)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/indexing.py", line 701, in __array__
    self._ensure_cached()
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/indexing.py", line 698, in _ensure_cached
    self.array = NumpyIndexingAdapter(np.asarray(self.array))
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/indexing.py", line 671, in __array__
    return np.asarray(self.array, dtype=dtype)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/core/indexing.py", line 572, in __array__
    return np.asarray(array[self.key], dtype=None)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/coding/variables.py", line 70, in __array__
    return self.func(self.array)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/coding/variables.py", line 217, in _scale_offset_decoding
    data = np.array(data, dtype=dtype, copy=True)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/coding/variables.py", line 70, in __array__
    return self.func(self.array)
  File "/import/AKWATERS/jrcermakiii/local/miniconda3/envs/gridTools/lib/python3.7/site-packages/xarray/coding/variables.py", line 137, in _apply_mask
    data = np.asarray(data, dtype=dtype)
numpy.core._exceptions.MemoryError: Unable to allocate 9.63 GiB for an array with shape (8760, 205, 1440) and data type float32
```
