import os
import keras
from keras.models import Sequential
from keras.layers.convolutional import Conv2D
from keras.layers.convolutional import MaxPooling2D
from keras.layers.core import Activation
from keras.layers.core import Flatten,Dropout
from keras.layers.core import Dense
from keras.datasets import cifar10
from keras.optimizers import RMSprop
from keras.callbacks import TensorBoard, ModelCheckpoint
from keras.preprocessing.image import ImageDataGenerator
import numpy as np

def network(input_shape, num_classes):
    model = Sequential()

    model.add(Conv2D(32, kernel_size=3, padding="same", input_shape=input_shape, activation="relu"))
    model.add(Conv2D(32, kernel_size=3, activation="relu"))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))
    model.add(Conv2D(64,kernel_size=3, padding="same", activation="relu"))
    model.add(Conv2D(64,kernel_size=3, activation="relu"))
    model.add(MaxPooling2D(pool_size=(2,2)))
    model.add(Dropout(0.25))
    model.add(Flatten())
    model.add(Dense(512,activation="relu"))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes))
    model.add(Activation("softmax"))
    return model

class CIFAR10Dataset():
    def __init__(self):
        self.image_shape = (32,32,3)
        self.num_classes = 10

    def get_batch(self):
        (x_train, y_train), (x_test, y_test) = cifar10.load_data()
        x_train, x_test = [self.preprocess(d) for d in [x_train,x_test]]
        y_train, y_test = [self.preprocess(d, label_data=True) for d in [y_train, y_test]]
        return x_train, y_train, x_test, y_test

    def preprocess(self, data, label_data=False):
        if label_data:
            data = keras.utils.to_categorical(data, self.num_classes)
        else:
            data = data.astype("float32")
            data /= 255
            shape = (data.shape[0],) + self.image_shape
            data = data.reshape(shape)
        return data

class Trainer():
    def __init__(self, model, loss, optimizer):
        self._target = model
        self._target.compile(loss=loss, optimizer=optimizer,metrics=["accuracy"])
        self.verbose = 1
        self.log_dir = os.path.join(os.path.dirname(__file__),"logdir")
        self.model_file_name = "cifar10_data_augmentation.hdf5"

    def train(self,x_train, y_train, batch_size, epochs, validation_split):
        if os.path.exists(self.log_dir):
            import shutil
            shutil.rmtree(self.log_dir)
        os.mkdir(self.log_dir)

        datagen = ImageDataGenerator(
            featurewise_center=False,
            samplewise_center=False,
            featurewise_std_normalization=False,
            samplewise_std_normalization=False,
            zca_whitening=False,
            rotation_range=0,
            width_shift_range=0.1,
            height_shift_range=0.1,
            horizontal_flip=True,
            vertical_flip=False)

        datagen.fit(x_train)

        indices = np.arange(x_train.shape[0])
        np.random.shuffle(indices)
        validation_size = int(x_train.shape[0] * validation_split)
        x_train, x_valid = x_train[indices[:-validation_size],:], x_train[indices[-validation_size:], :]
        y_train, y_valid = y_train[indices[:-validation_size],:], y_train[indices[-validation_size:], :]



        self._target.fit_generator(
                        datagen.flow(x_train, y_train,batch_size=batch_size),
                        steps_per_epoch=x_train.shape[0]//batch_size,
                        epochs=epochs,
                        validation_data = (x_valid,y_valid),
                        callbacks=[
                        TensorBoard(log_dir=self.log_dir),
                        ModelCheckpoint(os.path.join(self.log_dir,self.model_file_name),save_best_only=True)
                        ],
                        verbose=self.verbose,
                        workers=4
                        )

dataset = CIFAR10Dataset()
model = network(dataset.image_shape, dataset.num_classes)
x_train, y_train, x_test, y_test = dataset.get_batch()
trainer = Trainer(model, loss="categorical_crossentropy", optimizer=RMSprop())
trainer.train(x_train, y_train, batch_size=128, epochs=15, validation_split=0.2)

score = model.evaluate(x_test, y_test, verbose=0)
print("Test loss:", score[0])
print("Test accuracy: ", score[1])
