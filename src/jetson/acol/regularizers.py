from __future__ import absolute_import
import numpy as np
from keras import backend as K
from keras.regularizers import Regularizer
#from keras.utils.generic_utils import get_from_module
from acol.initializations import column_vstacked
import warnings

from keras.utils.generic_utils import deserialize_keras_object

from six.moves import zip

import tensorflow as tf

# Tr = K.theano.tensor.nlinalg.trace
# Diag = K.theano.tensor.nlinalg.ExtractDiag()
# Range = K.theano.tensor.ptp
# Tensordot = K.theano.tensor.tensordot
# Scan = K.theano.scan
# Arange = K.theano.tensor.arange

Tr = tf.trace
Diag = tf.diag_part
Range = tf.range
Tensordot = tf.tensordot
Scan = tf.scan
Arange = K.arange


class AcolRegularizer(Regularizer):
    """Regularizer for ACOL.

    # Arguments
        c1: Float; affinity factor.
        c2: Float; balance factor.
        c3: Float; coactivity factor.
        c4: Float; L2 regularization factor.
    """

    def __init__(self, c1=0., c2=0., c3=0., c4=0., balance_type=1):
        self.c1 = K.variable(c1)
        self.c2 = K.variable(c2)
        self.c3 = K.variable(c3)
        self.c4 = K.variable(c4)
        self.balance_type = balance_type

    def __call__(self, x):
        regularization = K.variable(0, dtype=K.floatx())
        Z = x
        n = K.shape(Z)[1]

        Z_bar = Z * K.cast(Z>0., K.floatx())
        # U = K.dot(Z_bar.T, Z_bar)
        U = K.dot(K.transpose(Z_bar), Z_bar)

        if self.balance_type == 1:
            v = K.reshape(Diag(U),(1, n))
        elif self.balance_type == 2:
            # v = K.sum(Z_bar, axis=0).reshape((1, n))
            v = K.reshape(K.sum(Z_bar, axis=0),(1, n))
        V = K.dot(K.transpose(v), v)

        affinity = (K.sum(U) - Tr(U)) / ((tf.cast(n,tf.float32)-1)*Tr(U) + K.epsilon())
        balance = (K.sum(V) - Tr(V)) / ((tf.cast(n,tf.float32)-1)*Tr(V) + K.epsilon())
        coactivity = balance #K.sum(U) - Tr(U)

        print(K.dtype(self.c1))
        print(self.c1)

        # if self.c1.get_value():
        #     regularization += self.c1 * affinity
        # if self.c2.get_value():
        #     regularization += self.c2 * (1-balance)
        # if self.c3.get_value():
        #     regularization += self.c3 * coactivity
        # if self.c4.get_value():
        #     regularization += K.sum(self.c4 * K.square(Z))
        #     #regularization += K.sum(self.c4 * K.square(Z_bar))

        if self.c1.value() is not None:
            regularization += self.c1 * affinity
        if self.c2.value() is not None:
            regularization += self.c2 * (1-balance)
        if self.c3.value() is not None:
            regularization += self.c3 * coactivity
        if self.c4.value() is not None:
            regularization += K.sum(self.c4 * K.square(Z))
            #regularization += K.sum(self.c4 * K.square(Z_bar))


        self.affinity = affinity
        self.balance = balance
        self.coactivity = coactivity
        self.reg = regularization

        return regularization

    def get_config(self):
        # return {'name': self.__class__.__name__,
        #         'c1': self.c1.get_value(),
        #         'c2': self.c2.get_value(),
        #         'c3': self.c3.get_value(),
        #         'c4': self.c4.get_value()}
        return {'name': self.__class__.__name__,
                'c1': self.c1.value(),
                'c2': self.c2.value(),
                'c3': self.c3.value(),
                'c4': self.c4.value()}


class AcolRegularizerNull(Regularizer):
    """Null regularizer for ACOL.

    # Arguments
        c1: Float; affinity factor.
        c2: Float; balance factor.
        c3: Float; coactivity factor.
        c4: Float; L2 regularization factor.
    """

    def __init__(self, c1=0., c2=0., c3=0., c4=0., k=1, balance_type=3):
        self.c1 = K.variable(c1)
        self.c2 = K.variable(c2)
        self.c3 = K.variable(c3)
        self.c4 = K.variable(c4)
        self.k = k
        self.balance_type = balance_type

    def __call__(self, x):
        regularization = K.variable(0, dtype=K.floatx())
        Z = x

        if self.balance_type < 5:

            n = K.shape(Z)[1]

            mask = identity_hvstacked((K.int_shape(Z)[1], self.k))

            Z_bar = Z * K.cast(Z>0., K.floatx())
            U = K.dot(Z_bar.T, Z_bar) * mask

            if self.balance_type == 3:
                v = Diag(U).reshape((1, n))
            elif self.balance_type == 4:
                v = K.sum(Z_bar, axis=0).reshape((1, n))
            V = K.dot(v.T, v)
            V = K.dot(v.T, v) * mask

            affinity = (K.sum(U) - Tr(U))/((self.k-1)*Tr(U) + K.epsilon())
            balance = (K.sum(V) - Tr(V))/((self.k-1)*Tr(V) + K.epsilon())
            coactivity = K.sum(U) - Tr(U)

        elif self.balance_type < 7:

            n = K.int_shape(Z)[1]
            mask = column_vstacked((n, self.k))

            Z_bar = K.dot(Z * K.cast(Z>0., K.floatx()), mask)
            U = K.dot(Z_bar.T, Z_bar)
            if self.balance_type == 5:
                v = Diag(U).reshape((1, self.k))
            elif self.balance_type == 6:
                v = K.sum(Z_bar, axis=0).reshape((1, self.k))
            V = K.dot(v.T, v)

            affinity = (K.sum(U) - Tr(U))/((self.k - 1) * Tr(U) + K.epsilon())
            balance = (K.sum(V) - Tr(V))/((self.k - 1) * Tr(V) + K.epsilon())
            coactivity = balance #K.sum(U) - Tr(U)

        # elif self.balance_type < 9:

        #     n = K.shape(Z)[1]
        #     Z_bar = K.reshape(Z * K.cast(Z>0., K.floatx()), (-1, self.k, n//self.k))
        #     U = Tensordot(Z_bar, Z_bar, axes=[0,0])

        #     partials, _  = Scan(calculate_partial_affinity_balance,
        #                    sequences=[Arange(U.shape[1])], non_sequences = [U, self.k, self.balance_type])

        #     affinity = K.mean(partials[0])
        #     balance = K.mean(partials[1])
        #     coactivity = K.mean(partials[1])

        if self.c1.value() is not None:
            regularization += self.c1 * affinity
        if self.c2.value() is not None:
            regularization += self.c2 * (1-balance)
        if self.c3.value() is not None:
            regularization += self.c3 * coactivity
        if self.c4.value() is not None:
            regularization += K.sum(self.c4 * K.square(Z))
            #regularization += K.sum(self.c4 * K.square(Z_bar))

        self.affinity = affinity
        self.balance = balance
        self.coactivity = coactivity
        self.reg = regularization

        return regularization

    def get_config(self):
        return {'name': self.__class__.__name__,
                'c1': self.c1.value(),
                'c2': self.c2.value(),
                'c3': self.c3.value(),
                'c4': self.c4.value()}


class AcolRegularizerForDropout(Regularizer):
    """Regularizer for ACOL.

    # Arguments
        c1: Float; affinity factor
    """

    def __init__(self, c1=0.):
        self.c1 = K.variable(c1)

    def __call__(self, x):
        regularization = K.variable(0, dtype=K.floatx())
        Z = x
        Z_bar = Z * K.cast(Z>0., K.floatx())

        if self.c1.get_value():
            regularization += self.c1 * K.sum(Range(Z_bar, axis=0))

        self.affinity = regularization
        self.balance = regularization
        self.coactivity = regularization
        self.reg = regularization

        return regularization

def identity_hvstacked(shape, scale=1, name=None, dim_ordering='th'):
    scale = shape[1]/float(shape[0])
    a = np.identity(int(1/scale))
    for i in range(1, shape[1]):
        a = np.concatenate((a, np.identity(int(1/scale))),axis=1)
    b = np.copy(a)
    for i in range(1, shape[1]):
        b = np.concatenate((b, a),axis=0)
    return K.variable(b, name=name)

def calculate_partial_affinity_balance(i, U, k, balance_type):
    U_partial = U[:,i,:,i]
    if balance_type.eval() == 7:
        v = Diag(U_partial).reshape((1,k))
    elif balance_type.eval() == 8:
        v = K.sum(U_partial, axis=0).reshape((1,k))
    V = K.dot(v.T, v)
    affinity = (K.sum(U_partial) - Tr(U_partial))/((k-1)*Tr(U_partial) + K.epsilon())
    balance = (K.sum(V) - Tr(V))/((k-1)*Tr(V) + K.epsilon())
    return affinity, balance

# Aliases.

def activity_acol(c1=1., c2=1., c3=0., c4=0.000001, balance_type=1):
    return AcolRegularizer(c1=c1, c2=c2, c3=c3, c4=c4, balance_type=balance_type)

def activity_acol_null(c1=1., c2=1., c3=0., c4=0.000001, k=1, balance_type=3):
    return AcolRegularizerNull(c1=c1, c2=c2, c3=c3, c4=c4, k=k, balance_type=balance_type)

def activity_acol_for_dropout(c1=0.00001):
    return AcolRegularizerForDropout(c1=c1)

# def get(identifier, kwargs=None):
#     return get_from_module(identifier, globals(), 'regularizer',
#                            instantiate=True, kwargs=kwargs)


def deserialize(config, custom_objects=None):
    return deserialize_keras_object(
      config,
      module_objects=globals(),
      custom_objects=custom_objects,
      printable_module_name='regularizer')


def get(identifier):
    if isinstance(identifier, dict):
        return deserialize(identifier)
    elif isinstance(identifier, six.string_types):
        config = {'class_name': str(identifier), 'config': {}}
        return deserialize(config)
    elif callable(identifier):
        return identifier
    else:
        raise ValueError('Could not interpret initializer identifier:', identifier)