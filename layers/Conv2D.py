from typing import Any, Union, Tuple

import tensorflow as tf
import keras.backend as K
from keras import activations
from keras.utils import conv_utils
from tensorflow.keras.layers import *
# pylint: disable=g-classes-have-attributes
from tensorflow.python.distribute.sharded_variable import ShardedVariable
from tensorflow.python.ops.variables import PartitionedVariable


@tf.keras.utils.register_keras_serializable()
class Conv2D(Layer):
    bias: Union[Union[PartitionedVariable, ShardedVariable, Conv2D], Any]
    kernel: Union[Union[PartitionedVariable, ShardedVariable, Conv2D], Any]

    def __init__(self, filters: int = 32, kernel_size: Tuple[int, int] = (3, 3), strides: Tuple[int, int] = (1, 1), padding: bool ='VALID',
                 activation='relu',
                 dilation_rate=(1, 1), batch_size=1, **kwargs):

        self.filters = filters
        self.bias = None
        self.kernel_size = kernel_size
        self.kernel = None
        self.strides = strides
        self.padding = padding
        if activation is not None:
            self.activation = activations.get(activation)
        else:
            self.activation = None
        self.dilation_rate = dilation_rate
        self.batch_size = batch_size
        if K.image_data_format() == 'channels_first':
            self.channel_axis = 0
        else:
            self.channel_axis = -1
        super(Conv2D, self).__init__(**kwargs)

    def build(self, input_shape):
        kernel_shape = self.kernel_size + (input_shape[self.channel_axis], self.filters)
        self.bias = self.add_weight(name='conv_bias',
                                    shape=(self.filters,),
                                    dtype='float32',
                                    initializer=tf.zeros_initializer(),
                                    trainable=True)
        self.kernel = self.add_weight(name='kernel',
                                      shape=kernel_shape,
                                      initializer=tf.keras.initializers.GlorotUniform(),
                                      trainable=True)
        super(Conv2D, self).build(input_shape)

    def call(self, x, **kwargs):
        y = tf.keras.backend.conv2d(x, self.kernel)
        y = K.bias_add(y, self.bias)
        if self.activation is not None:
            y = self.activation(y)
        return y

    def compute_output_shape(self, input_shape):
        batch_size = input_shape[0]
        convX = conv_utils.conv_output_length(
            input_shape[1],
            self.kernel_size[0],
            padding=self.padding,
            stride=self.strides[0],
            dilation=self.dilation_rate[0]
        )
        convY = conv_utils.conv_output_length(
            input_shape[2],
            self.kernel_size[1],
            padding=self.padding,
            stride=self.strides[1],
            dilation=self.dilation_rate[1]
        )
        return batch_size, convX, convY, self.filters

    def get_config(self):
        config = super().get_config()
        config.update({
            "filters": self.filters,
            "kernel_size": self.kernel_size,
            "strides": self.strides,
            "padding": self.padding,
            "activation": self.activation,
            "dilation_rate": self.dilation_rate,
            "batch_size": self.batch_size,
        })
        return config



if __name__ == '__main__':
    def create_model():
        model = tf.keras.models.Sequential([
            tf.keras.layers.Input(shape=(224, 224, 3)),
            Conv2D(),
            Conv2D(),
        ])
        return model


    def create_keras_model():
        model = tf.keras.models.Sequential([
            tf.keras.layers.Input(shape=(224, 224, 3)),
            tf.keras.layers.Conv2D(32, (3, 3)),
            tf.keras.layers.Conv2D(32, (3, 3)),
        ])
        return model


    keras = create_keras_model()
    print(keras.summary())
    model = create_model()
    print(model.summary())
    h = tf.keras.models.load_model('my_model', custom_objects=...)
