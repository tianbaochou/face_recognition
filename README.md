## Face Recognition

The first version of code fork from [here](https://github.com/yeziyang1992/Face_Recognition_Client.git) and add some useful function
I will remove some ugly function and re-coding later...
I prefer pytorch framework, so the final version will support 
pytorch 1.x. Anyway, thanks to the authors.

### Request

+ Tensorflow-gpu >= 1.10

+ opencv >= 2.4.5

+ dlib

## Support:

+ Linux and Window platform
+ Chinese name
+ CPU and GPU (请等待...)

### Usage:

+ run the face recognition
```python
python main.py
```

+ train model

```python
python train.py --epochs 1000
```

TODO:

- [ ] Pytorch CNN version
- [ ] Train Backend network using recently face network
- [ ] Using more fast face detector
- [ ] Store face into encoder-format

