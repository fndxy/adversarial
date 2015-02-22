import os

import numpy as np
from pylearn2.datasets import dense_design_matrix
from pylearn2.expr.preprocessing import global_contrast_normalize
from pylearn2.utils import contains_nan, image
from pylearn2.utils.rng import make_np_rng


class LFW(dense_design_matrix.DenseDesignMatrix):
    """
    TODO
    """

    def __init__(self, lfw_path, filelist_path, embedding_file=None,
                 center=False, scale=False,
                 gcn=None, shuffle=False, rng=None, seed=132987,
                 axes=('b', 0, 1, 'c'), img_shape=(3, 250, 250)):
        self.axes = axes

        self.img_shape = img_shape
        C, H, W = img_shape
        self.img_size = np.prod(self.img_shape)

        files = []
        with open(filelist_path, 'r') as filelist_f:
            files = [line.strip() for line in filelist_f]

        # Load raw pixel integer values
        dtype = 'uint8'
        X = np.zeros((len(files), W, H, C), dtype=dtype)
        img_ids = []

        for i, line in enumerate(files):
            img_path, img_id = line.strip().split()
            img_ids.append(img_id)

            full_path = os.path.join(lfw_path, img_path)
            im = image.load(full_path, rescale_image=False, dtype=dtype)

            # Handle grayscale images which may not have RGB channels
            if len(im.shape) == 2:
                W, H = im.shape

                # Repeat image 3 times across axis 2
                im = im.reshape(W, H, 1).repeat(3, 2)

            # Swap color channel to front
            X[i] = im

        # Cast to float32, center / scale if necessary
        X = np.cast['float32'](X)

        # Create dense design matrix from topological view
        X = X.reshape(X.shape[0], -1)

        if center and scale:
            X[:] -= 127.5
            X[:] /= 127.5
        elif center:
            X[:] -= 127.5
        elif scale:
            X[:] /= 255.

        self.gcn = gcn
        if gcn is not None:
            gcn = float(gcn)
            X = global_contrast_normalize(X, scale=gcn)

        if shuffle:
            rng = make_np_rng(rng, seed, which_method='permutation')
            rand_idx = rng.permutation(len(X))
            X = X[rand_idx]

        # Load embeddings if provided
        Y = None
        if embedding_file is not None:
            embeddings = np.load(embedding_file)['arr_0']
            assert embeddings.shape[0] >= len(files)

            Y = embeddings[img_ids]

        # create view converting for retrieving topological view
        self.view_converter = dense_design_matrix.DefaultViewConverter((W, H, C), axes)

        # init super class
        super(LFW, self).__init__(X=X, y=Y)

        assert not contains_nan(self.X)
