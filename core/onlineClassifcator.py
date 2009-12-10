from classificationMgr import *
import svm_new as lasvm

class OnlineClassifier(ClassifierBase):
    def __init__(self):
        pass
    def start(self,features,labels,ids):
        pass
    def addData(self,features,labels,ids):
        pass
    def removeData(self,ids):
        pass
    def fastLearn(self):
        pass
    def improveSolution(self):
        pass
    def predict(self,features):
        pass

class OnlineLaSvm(OnlineClassifier):
    def __init__(self,cacheSize=1000):
        self.cacheSize=cacheSize
        self.svm=None

    def start(self,features,labels,ids):
        labels=labels*2-1;
        self.svm=lasvm.createLaSvmMultiPar(1.0/features.shape[1],features.shape[1],1.0,0.001,self.cacheSize,True)
        self.addData(features,labels,ids)
        svm.enableResampleBorder(0.1)

    def addData(self,features,labels,ids):
        if(self.svm==None):
            raise RuntimeError("run \"start\" before addData")
        svm.addData(features,labels,ids)

    def removeData(self,ids):
        if self.svm==None:
            raise RuntimeError("run \"start\" first")
        svm.removeData(ids)

    def fastLearn(self):
        if self.svm==None:
            raise RuntimeError("run \"start\" first")
        svm.fastLearn(2,1,True)
        svm.finish(True)

    def improveSolution(self):
        if self.svm==None:
            raise RuntimeError("run \"start\" first")
        svm.optimizeKernelStep(0)

    def predict(self,features):
        return svm.predict(features)



