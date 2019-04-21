import joblib
import numpy as np
import pandas as pd
import pytest

import anndata as ad


# -------------------------------------------------------------------------------
# Some test data
# -------------------------------------------------------------------------------

X_list = [    # data matrix of shape n_obs x n_vars
    [1, 2, 3], [4, 5, 6], [7, 8, 9]]

obs_dict = {  # annotation of observations / rows
    'row_names': ['name1', 'name2', 'name3'],  # row annotation
    'oanno1': ['cat1', 'cat2', 'cat2'],        # categorical annotation
    'oanno2': ['o1', 'o2', 'o3'],              # string annotation
    'oanno3': [2.1, 2.2, 2.3]}                 # float annotation

var_dict = {  # annotation of variables / columns
    'vanno1': [3.1, 3.2, 3.3]}

uns_dict = {  # unstructured annotation
    'oanno1_colors': ['#000000', '#FFFFFF'],
    'uns2': ['some annotation']}


# -------------------------------------------------------------------------------
# The test functions
# -------------------------------------------------------------------------------

@pytest.fixture
def adata():
    adata = ad.AnnData(np.empty((100, 100)))
    adata.obsm['o'] = np.zeros((100, 50))
    adata.varm['o'] = np.zeros((100, 50))
    return adata

def test_views():
    X = np.array(X_list)
    adata = ad.AnnData(X, obs=obs_dict, var=var_dict, uns=uns_dict, dtype='int32')

    assert adata[:, 0].isview
    assert adata[:, 0].X.tolist() == [1, 4, 7]

    adata[:2, 0].X = [0, 0]

    assert adata[:, 0].X.tolist() == [0, 0, 7]

    adata_subset = adata[:2, [0, 1]]

    assert adata_subset.isview
    # now transition to actual object
    adata_subset.obs['foo'] = range(2)
    assert not adata_subset.isview

    assert adata_subset.obs['foo'].tolist() == list(range(2))


# These tests could probably be condensed into a fixture based test for obsm and varm
def test_set_obsm_key(adata):
    init_hash = joblib.hash(adata)

    orig_obsm_val = adata.obsm['o'].copy()
    subset_obsm = adata[:50]
    assert subset_obsm.isview
    subset_obsm.obsm['o'] = np.ones((50, 20))
    assert not subset_obsm.isview
    assert np.all(adata.obsm["o"] == orig_obsm_val)

    assert init_hash == joblib.hash(adata)


def test_set_varm_key(adata):
    init_hash = joblib.hash(adata)

    orig_varm_val = adata.varm['o'].copy()
    subset_varm = adata[:, :50]
    assert subset_varm.isview
    subset_varm.varm['o'] = np.ones((50, 20))
    assert not subset_varm.isview
    assert np.all(adata.varm["o"] == orig_varm_val)

    assert init_hash == joblib.hash(adata)

def test_set_obsm(adata):
    init_hash = joblib.hash(adata)

    dim0_size = np.random.randint(2, adata.shape[0] - 1)
    dim1_size = np.random.randint(1, 99)
    orig_obsm_val = adata.obsm["o"].copy()
    subset_idx = np.random.choice(adata.obs_names, dim0_size, replace=False)

    subset =  adata[subset_idx, :]
    assert subset.isview
    subset.obsm = {"o": np.ones((dim0_size, dim1_size))}
    assert not subset.isview
    assert np.all(orig_obsm_val == adata.obsm["o"])  # Checking for mutation
    assert np.all(subset.obsm["o"] == np.ones((dim0_size, dim1_size)))

    subset = adata[subset_idx, :]
    subset_hash = joblib.hash(subset)
    with pytest.raises(ValueError):
        subset.obsm = {"o": np.ones((dim0_size + 1, dim1_size))}
    with pytest.raises(ValueError):
        subset.varm = {"o": np.ones((dim0_size - 1, dim1_size))}
    assert subset_hash == joblib.hash(subset)

    assert init_hash == joblib.hash(adata)  # Only modification have been made to a view


def test_set_varm(adata):
    init_hash = joblib.hash(adata)

    dim0_size = np.random.randint(2, adata.shape[0] - 1)
    dim1_size = np.random.randint(1, 99)
    orig_varm_val = adata.varm["o"].copy()
    subset_idx = np.random.choice(adata.var_names, dim0_size, replace=False)

    subset = adata[:, subset_idx]
    assert subset.isview
    subset.varm = {"o": np.ones((dim0_size, dim1_size))}
    assert not subset.isview
    assert np.all(orig_varm_val == adata.varm["o"])  # Checking for mutation
    assert np.all(subset.varm["o"] == np.ones((dim0_size, dim1_size)))

    subset = adata[:, subset_idx]
    subset_hash = joblib.hash(subset)
    with pytest.raises(ValueError):
        subset.varm = {"o": np.ones((dim0_size + 1, dim1_size))}
    with pytest.raises(ValueError):
        subset.varm = {"o": np.ones((dim0_size - 1, dim1_size))}
    assert subset_hash == joblib.hash(subset)  # subset should not be changed by failed setting

    assert init_hash == joblib.hash(adata)
