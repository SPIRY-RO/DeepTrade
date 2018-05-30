import tensorflow as tf
from numpy.random import RandomState

if __name__ == "__main__":
    #定义每次训练数据batch的大小为8，防止内存溢出
    batch_size = 8
    #定义神经网络的参数
    w1 = tf.Variable(tf.random_normal([2,3],stddev=1,seed=1))
    w2 = tf.Variable(tf.random_normal([3,1],stddev=1,seed=1))
    #定义输入和输出
    x = tf.placeholder(tf.float32,shape=(None,2),name="x-input")
    y_ = tf.placeholder(tf.float32,shape=(None,1),name="y-input")
    #定义神经网络的前向传播过程
    a = tf.matmul(x,w1)
    y = tf.matmul(a,w2)
    #定义损失函数和反向传播算法
    #使用交叉熵作为损失函数
    #tf.clip_by_value(t, clip_value_min, clip_value_max,name=None)
    #基于min和max对张量t进行截断操作，为了应对梯度爆发或者梯度消失的情况
    cross_entropy = -tf.reduce_mean(y_ * tf.log(tf.clip_by_value(y,1e-10,1.0)))
    # 使用Adadelta算法作为优化函数，来保证预测值与实际值之间交叉熵最小
    train_step = tf.train.AdamOptimizer(0.001).minimize(cross_entropy)
    #通过随机函数生成一个模拟数据集
    rdm = RandomState(1)
    # 定义数据集的大小
    dataset_size = 128
    # 模拟输入是一个二维数组
    X = rdm.rand(dataset_size,2)
    #定义输出值，将x1+x2 < 1的输入数据定义为正样本
    Y = [[int(x1+x2 < 1)] for (x1,x2) in X]
    #创建会话运行TensorFlow程序
    with tf.Session() as sess:
        #初始化变量  tf.initialize_all_variables()
        init = tf.initialize_all_variables()
        sess.run(init)
        #设置神经网络的迭代次数
        steps = 5000
        for i in range(steps):
            #每次选取batch_size个样本进行训练
            start = (i * batch_size) % dataset_size
            end = min(start + batch_size,dataset_size)
            #通过选取样本训练神经网络并更新参数
            sess.run(train_step,feed_dict={x:X[start:end],y_:Y[start:end]})
            #每迭代1000次输出一次日志信息
            if i % 1000 == 0 :
                # 计算所有数据的交叉熵
                total_cross_entropy = sess.run(cross_entropy,feed_dict={x:X,y_:Y})
                # 输出交叉熵之和
                print("After %d training step(s),cross entropy on all data is %g"%(i,total_cross_entropy))
                #输出参数w1
        print(w1.eval(session=sess))
        #输出参数w2
        print(w2.eval(session=sess))