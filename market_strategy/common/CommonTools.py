class CommonTools:
    def __init__(self):
        pass

    @staticmethod
    def as_num(x,num):
        str='{:.%df}'%(num)
        y=str.format(x) # nf表示保留n位小数点的float型
        return(y)
