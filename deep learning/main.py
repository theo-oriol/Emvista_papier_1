from model import LSTM,Camembert
from dataset import data_extraction
import tqdm
from argparse import Namespace
import torch 
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
import numpy as np 
from sklearn.metrics import confusion_matrix

param = Namespace(
    train = "train.csv",
    valid = "valid.csv",
    token = "camembert-base",
    batch_size = 16,
    em_sz = 100,
    nh = 500,
    nl = 3,
    epochs=  4  
)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

train_dl , valid_dl, len_vocab, labels = data_extraction(param.train,param.valid,device,param.batch_size)

model = LSTM(len_vocab,len(labels),param.nh, emb_dim=param.em_sz).to(device)


opt = optim.Adam(model.parameters(), lr=1e-2)
loss_func = nn.BCEWithLogitsLoss()


for epoch in range(1, param.epochs + 1):
    running_loss = 0.0
    running_corrects = 0
    model.train() 
    
    true_pred = []
    model_pred = []
    
    for x, y in tqdm.tqdm(train_dl):
 
        length = len(y)
        y = torch.nn.functional.one_hot(y.to(torch.int64), len(labels))
        y = y.reshape(length,len(labels))
        opt.zero_grad()

        preds = model(x)
        y = y.type_as(preds)
        loss = loss_func(preds, y)
        loss.backward()
        opt.step()
        
        running_loss += loss.item() * x.size(0)
        
    epoch_loss = running_loss / len(train_dl)
    
    val_loss = 0.0
    class_correct = 0
    class_total = 0
    model.eval() 

    for x, y in tqdm.tqdm(valid_dl):
        preds = model(x)

        length = len(y)
        y = torch.nn.functional.one_hot(y.to(torch.int64), len(labels))
        y = y.reshape(length,len(labels))
        y = y.type_as(preds)

        loss = loss_func(preds, y)
        val_loss += loss.item() * x.size(0)

        for i in range(len(y)):
            pred = torch.argmax(y[i])
            y_pred =  torch.argmax(preds[i])
            if pred  == y_pred :
                class_correct += 1
            class_total +=1

            true_pred.append(y_pred.item())
            model_pred.append(pred.item())
        
    if epoch == param.epochs :
        print(labels)
        #print(confusion_matrix(true_pred, model_pred))
        matrice = {}
        for y_true,y_pred in zip(true_pred,model_pred):
            if labels[y_pred] not in matrice :
                matrice[labels[y_pred]] = []
            
            if y_true == y_pred :
                matrice[labels[y_pred]].append(1)
            else :
                matrice[labels[y_pred]].append(0)

        for el in matrice : 
            matrice[el] = np.mean(matrice[el])
        print(matrice)




            

    val_loss /= len(valid_dl)
    accuracy = class_correct / class_total 
    print('Epoch: {}, Training Loss: {:.4f}, Validation Loss: {:.4f}, Accuracy {:.4f}'.format(epoch, epoch_loss, val_loss,accuracy))


    