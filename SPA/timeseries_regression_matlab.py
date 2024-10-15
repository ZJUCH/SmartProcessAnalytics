# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 09:38:56 2019

@author: Weike (Vicky) Sun vickysun@mit.edu/weike.sun93@gmail.com
(c) 2020 Weike Sun, all rights reserved
"""

"""
This file call MATLAB for state space model fitting,
There are two modes:
    (1) Single training set, with option of testing data
    (2) Multiple training sets, with option of testing data
"""

import numpy as np
import matlab.engine
import scipy.io as sio
import os
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import matplotlib.style
import matplotlib as mpl
mpl.style.use('default')

def timeseries_matlab_single(X, y, X_test=None, y_test=None, train_ratio = 1,\
                      maxorder = 10, mynow = 1, steps = 10, plot = True):
    '''This function fits the state space model using matlab n4sid for training data X, y of first training ratio data,
    and use rest (1-ratio_data) for forcasting. There can also be test data to test the fitted state space model
    Input:
        X: training data predictors numpy array: Nxm
        y: training data response numy array: Nx1
        X_test: testing data predictors numpy arrray: N_testxm
        y_test: testing data response numpy array: N_test x 1
        train_ratio: float, portion of training data used to train the model, and the rest is used as validation data
        maxorder: maximum state space order used, default = 10
        mynow: instantaneous effect of u on y in state space model, 1: yes, 0: no, defualt 1
        steps: number of steps considered for prediction
        plot: flag for plotting results or not, default TRUE
        
        
    Output:
        fitted system:
            my_matlab_ss: sys, A, B, C, D, K
        
            
        Preditction results:
            MSE_train, MSE_val, MSE_test with differnt prediction steps
            
                prediction: prediction by final optimal model, Num_steps X timeinstances, the frist row is one step ahead by Kalman
                error: the error y_predict-y_real
    '''

    print('======== Pre-process Data =========')
    n_train = round(train_ratio*np.shape(y)[0])

    scaler = StandardScaler()
    scaler.fit(X[:n_train])
    X = scaler.transform(X)
        
    scalery = StandardScaler()
    scalery.fit(y[:n_train])
    y=scalery.transform(y)
        

    if y_test is not None:
        test = 1
        X_test = scaler.transform(X_test)
        y_test = scalery.transform(y_test)
    else:
        test = 0





    ###Save Data in desired form to mydata.mat, which contains mydata as a matrix of size (m_y+m_x)xN, where y as the first row
    mydata=np.vstack((np.transpose(y),np.transpose(X)))    
    sio.savemat('mydata.mat', {'mydata':mydata})
    
    if test:
        ###Save test Data in desired form to mydataval.mat
        mydatatest=np.vstack((np.transpose(y_test),np.transpose(X_test)))    
        sio.savemat('mydatatest.mat', {'mydatatest':mydatatest})

    
    m_y = np.shape(y)[1]
    ###Save parameters in a file
    sio.savemat('myparams.mat', {'mydimy':m_y, 'mynow':mynow,'maxorder':maxorder, 'test':test, 'steps':steps, 'n_train':n_train})
     
    print('=========Model Training==========')
    ###Call the matlab script
    eng = matlab.engine.start_matlab()
    eng.cd(os.getcwd())
    #eng.addpath(url, nargout=0)
    eng.Matlab_singleset_fit_test(nargout=0)
    
    eng.quit()
    
    ###Read Results and do Plots
    #the parameters are saved in myresults
    myresults_train = sio.loadmat('myresults_train.mat')
    y_predict_train = myresults_train['prediction']
    y_real_train = y[:n_train].transpose()
    train_error = myresults_train['error']
    MSE_train = myresults_train['MSE']
    
    if train_ratio < 1:
        myresults_val = sio.loadmat('myresults_val.mat')
        y_predict_val = myresults_val['prediction_val']
        y_real_val = y[n_train:].transpose()
        val_error = myresults_val['error_val']
        MSE_val = myresults_val['MSE_val']
    else:
        y_predict_val =None
        val_error = None
        MSE_val =None
        
    if test:
        myresults_test = sio.loadmat('myresults_test.mat')
        y_predict_test = myresults_test['prediction_test']
        y_real_test = y_test.transpose()
        test_error = myresults_test['error_test']
        MSE_test = myresults_test['MSE_test']    
    else:
        y_predict_test =None
        test_error = None
        MSE_test =None
        
    
    
    #plot the prediction results
    if plot:
        import matplotlib
        cmap = matplotlib.cm.get_cmap('Paired')
        
        s=12
        
        print('=====Plot Data for prediction=======')
        #plot the prediction vs real
        for i in range(steps):
            for j in range(m_y):
        
                plt.figure(figsize=(5,3))
                plt.plot(y_real_train[j], color= cmap(j*2+1), label= 'real')
                plt.plot(y_predict_train[m_y*i+j], '--', color= 'xkcd:coral', label = 'prediction')
                plt.title('Training data' + str(i+1) +'-step prediction for y' + str(j+1),fontsize=s)
                plt.xlabel('Time index',fontsize=s)
                plt.ylabel('y',fontsize=s)
                plt.legend(fontsize=s)
                plt.tight_layout()
                plt.savefig('Train_var_' + str(j+1)+'_step_'+str(i+1)+'.png', dpi = 600,bbox_inches='tight')
                
                if train_ratio < 1:
                    plt.figure(figsize=(5,3))
                    plt.plot(y_real_val[j], color= cmap(j*2+1), label= 'real')
                    plt.plot(y_predict_val[m_y*i+j], '--', color= 'xkcd:coral',label = 'prediction')
                    plt.title('Validation data ' + str(i+1) +'-step prediction for y' + str(j+1),fontsize=s)
                    plt.xlabel('Time index',fontsize=s)
                    plt.ylabel('y',fontsize=s)
                    plt.legend(fontsize=s)
                    plt.tight_layout()                    
                    plt.savefig('Val_var_' + str(j+1)+'_step_'+str(i+1)+'.png', dpi = 600,bbox_inches='tight')

                if test:
                    plt.figure(figsize=(5,3))
                    plt.plot(y_real_test[j], color= cmap(j*2+1), label= 'real')
                    plt.plot(y_predict_test[m_y*i+j], '--',color= 'xkcd:coral', label = 'prediction')
                    plt.title('Test data ' + str(i+1) +'-step prediction for y' + str(j+1),fontsize=s)
                    plt.xlabel('Time index',fontsize=s)
                    plt.ylabel('y',fontsize=s)
                    plt.legend(fontsize=s)
                    plt.tight_layout()                    
                    plt.savefig('Test_var_' + str(j+1)+'_step_'+str(i+1)+'.png', dpi = 600,bbox_inches='tight')

                
#                plt.close('all')
        
        #plot fitting errors
        
        max_limit=np.nanmax(train_error[-m_y:],axis=1)
        min_limit=np.nanmin(train_error[-m_y:],axis=1)
        
        fig, axs = plt.subplots(steps,m_y,figsize=(3*m_y,2*steps))
      
        if m_y>1:
            for i in range(steps):
                for j in range(m_y):
                    axs[i,j].plot(train_error[m_y*i+j], color= cmap(j*2+1))
                    axs[i,j].set_title('Training data' + str(i+1) +'-step error for y' + str(j+1), fontsize=s)
                    axs[i,j].set_ylim(min_limit[j]-abs(min_limit[j])*0.5,max_limit[j]*1.5)
                    if i is steps-1:
                        axs[i,j].set_xlabel('Time index', fontsize=s)              
            fig.tight_layout()
            plt.savefig('Train error.png', dpi = 600,bbox_inches='tight')
            
            
            if train_ratio < 1: 
                
                max_limit=np.nanmax(val_error[-m_y:],axis=1)
                min_limit=np.nanmin(val_error[-m_y:],axis=1)
                fig1, axs1 = plt.subplots(steps,m_y,figsize=(3*m_y,2*steps))
                
                for i in range(steps):
                    for j in range(m_y):
                        axs1[i,j].plot(val_error[m_y*i+j], color= cmap(j*2+1))
                        axs1[i,j].set_title('Val data' + str(i+1) +'-step error for y' + str(j+1), fontsize=s)
                        axs1[i,j].set_ylim(min_limit[j]-abs(min_limit[j])*0.5,max_limit[j]*1.5)
                        if i is steps-1:
                            axs1[i,j].set_xlabel('Time index', fontsize=s)                
                fig1.tight_layout()
                plt.savefig('Val error.png', dpi=600,bbox_inches='tight')
                
                
            if test:  
                max_limit=np.nanmax(test_error[-m_y:],axis=1)
                min_limit=np.nanmin(test_error[-m_y:],axis=1)
                fig2, axs2 = plt.subplots(steps,m_y, figsize=(3*m_y,2*steps))
                
                for i in range(steps):
                    for j in range(m_y):
                        axs2[i,j].plot(test_error[m_y*i+j], color= cmap(j*2+1))
                        axs2[i,j].set_title('Test data' + str(i+1) +'-step error for y' + str(j+1), fontsize=s)
                        axs2[i,j].set_ylim(min_limit[j]-abs(min_limit[j])*0.5,max_limit[j]*1.5)
                        if i is steps-1:
                            axs2[i,j].set_xlabel('Time index', fontsize=s)                
                fig2.tight_layout()
                plt.savefig('Test error.png', dpi=600,bbox_inches='tight')        
        else:
            for i in range(steps):
                axs[i].plot(train_error[m_y*i], color= cmap(1))
                axs[i].set_title('Training data' + str(i+1) +'-step error for y' + str(1), fontsize=s)
                axs[i].set_ylim(min_limit-abs(min_limit)*0.5,max_limit*1.5)
                if i is steps-1:
                    axs[i].set_xlabel('Time index', fontsize=s)              
            fig.tight_layout()
            plt.savefig('Train error.png', dpi = 600,bbox_inches='tight')
            
            
            if train_ratio < 1:               
                max_limit=np.nanmax(val_error[-m_y:],axis=1)
                min_limit=np.nanmin(val_error[-m_y:],axis=1)
                fig1, axs1 = plt.subplots(steps,m_y,figsize=(3*m_y,2*steps))
                
                for i in range(steps):                   
                    axs1[i].plot(val_error[m_y*i], color= cmap(1))
                    axs1[i].set_title('Val data' + str(i+1) +'-step error for y' + str(1), fontsize=s)
                    axs1[i].set_ylim(min_limit-abs(min_limit)*0.5,max_limit*1.5)
                    if i is steps-1:
                        axs1[i].set_xlabel('Time index', fontsize=s)                
                fig1.tight_layout()
                plt.savefig('Val error.png', dpi=600,bbox_inches='tight')
                
                
            if test:  
                max_limit=np.nanmax(test_error[-m_y:],axis=1)
                min_limit=np.nanmin(test_error[-m_y:],axis=1)
                fig2, axs2 = plt.subplots(steps,m_y,figsize=(3*m_y,2*steps))
                
                for i in range(steps):
                    axs2[i].plot(test_error[m_y*i], color= cmap(1))
                    axs2[i].set_title('Test data' + str(i+1) +'-step error for y' + str(1), fontsize=s)
                    axs2[i].set_ylim(min_limit-abs(min_limit)*0.5,max_limit*1.5)
                    if i is steps-1:
                        axs2[i].set_xlabel('Time index', fontsize=s)                
                fig2.tight_layout()
                plt.savefig('Test error.png', dpi=600,bbox_inches='tight')        
        
        
        #MSE for prediction results over different steps
        for i in range(m_y):
            plt.figure(figsize=(3,2))
            plt.plot(MSE_train[i], 'd-', color = cmap(i*2+1))
            plt.title('MSE for y' + str(i+1) +' training prediction', fontsize = s)
            plt.xlabel('k-step ahead', fontsize = s)
            plt.ylabel('MSE', fontsize = s)
            plt.savefig('MSE_train '+str(i+1)+'.png', dpi=600,bbox_inches='tight')        
    
        if train_ratio < 1: 
            for i in range(m_y):
                plt.figure(figsize=(3,2))
                plt.plot(MSE_val[i], 'd-', color = cmap(i*2+1))
                plt.title('MSE for y' + str(i+1) +' validation prediction', fontsize = s)
                plt.xlabel('k-step ahead', fontsize = s)
                plt.ylabel('MSE', fontsize = s)
                plt.savefig('MSE_val '+str(i+1)+'.png', dpi=600,bbox_inches='tight')  

                
        if test:
            for i in range(m_y):
                plt.figure(figsize=(3,2))
                plt.plot(MSE_test[i], 'd-', color = cmap(i*2+1))
                plt.title('MSE for y' + str(i+1) +' testing prediction', fontsize = s)
                plt.xlabel('k-step ahead', fontsize = s)
                plt.ylabel('MSE', fontsize = s)
                plt.savefig('MSE_test'+str(i+1)+'.png', dpi=600,bbox_inches='tight')



    myresults = sio.loadmat('my_matlab_ss')
    optimal_params = {}
    optimal_params['ord'] = myresults['final_order']
    optimal_params['method'] = myresults['final_model']

        
    return(optimal_params, myresults, MSE_train, MSE_val, MSE_test, y_predict_train, y_predict_val, y_predict_test, train_error, val_error, test_error)
    
    
    
    
    
    
    
    
    
    
    
    
    
def timeseries_matlab_multi(X, y, timeindex, num_series, X_test=None, y_test=None, train_ratio = 0.8,\
                       maxorder = 10, mynow = 1, steps = 10, plot = True):

    '''This function fits the CVA-state space model for training data X, y of first training ratio data,
    and use rest (1-ratio_data) for forcasting. There can also be test data to test the fitted state space model
    Input:
        X: dictionary of training data predictors numpy array: Nxm, composed of all the data (several time seireses)
        y: dictionary of training data response numy array: Nx1, composed of all the data (several time seireses)
        timeindex: dictionary, time invterval for each seperate time series, stored in one dictionary, labeled by times seires index, which has shape (N,)
        train_ratio: float, portion of training data used to train the model, and the rest is used as validation data, is applied to every time seires
        num_series: total number of time series contained
        X_test: testing data predictors numpy arrray: N_testxm
        y_test: testing data response numpy array: N_test x 1

        maxorder: maximum state space order used, default = 10
        mynow: instantaneous effect of u on y in state space model, 1: yes, 0: no, defualt 1
        steps: number of steps considered for prediction
        plot: flag for plotting results or not, default TRUE
        
        
    Output:
        fitted system:
            my_matlab_ss: sys, A, B, C, D, K
        
            
        Preditction results:
            MSE_train, MSE_val,  MSE_test with differnt prediction steps
            
                prediction: prediction by final optimal model, Num_steps X timeinstances, the frist row is one step ahead by Kalman
                error: the error y_predict-y_real

    '''

    cum = 0
    ##scale data
    for i in range(num_series):
        num = np.shape(timeindex[i+1])[0]       
        num_up_to = round(train_ratio*num)
        if i == 0:
            y_scale = y[cum:cum+num_up_to]
            X_scale = X[cum:cum+num_up_to]
        else:
            y_scale = np.vstack((y_scale, y[cum:cum+num_up_to]))
            X_scale = np.vstack((X_scale,X[cum:cum+num_up_to]))
        cum += num

    scaler = StandardScaler()
    scaler.fit(X_scale)
    X = scaler.transform(X)
        
    scalery = StandardScaler()
    scalery.fit(y_scale)
    y=scalery.transform(y)


    
    ###Save Data in desired form to mydata.mat, which contains mydata as a matrix of size (m_y+m_x)xN, where y as the first row
    cum = 0
    y_real_train = {}
    y_real_val = {}

    for i in range(num_series):
        num = np.shape(timeindex[i+1])[0]       
        num_up_to = round(train_ratio*num)
         
        d = np.vstack((np.transpose(y[cum:cum+num_up_to]),np.transpose(X[cum:cum+num_up_to])))
        sio.savemat('filist' + str(i+1)+'.mat', {'d':d, 'timint':timeindex[i+1][:num_up_to]})
        y_real_train[i+1] = y[cum:cum+num_up_to].transpose()
        
        if train_ratio<1:
            d = np.vstack((np.transpose(y[cum:cum+num]),np.transpose(X[cum:cum+num])))
            sio.savemat('filist_whole' + str(i+1)+'.mat', {'d':d, 'timint':timeindex[i+1]})
            y_real_val[i+1] = y[cum+num_up_to:cum+num].transpose()
            
        cum += num

    
    if y_test is not None:
        X_test = scaler.transform(X_test)
        y_test = scalery.transform(y_test)
        
        ###Save test Data in desired form to mydataval.mat
        mydatatest=np.vstack((np.transpose(y_test),np.transpose(X_test)))    
        sio.savemat('mydatatest.mat', {'mydatatest':mydatatest})
        test = 1
    else:
        test = 0
    
    
    m_y = np.shape(y)[1]
    ###Save parameters in a file
    sio.savemat('myparams.mat', {'mydimy':m_y, 'mynow':mynow, 'maxorder':maxorder, 'test':test, 'steps':steps, 'train_ratio':train_ratio, 'num_series':num_series})
     
    
    ###Call the matlab script
    eng = matlab.engine.start_matlab()
    eng.cd(os.getcwd())
    #eng.addpath(url, nargout=0)
    eng.Matlab_multiset_fit_test(nargout=0)
    
    

    '''load prediction restuls for training and validation'''
    y_predict_train = {}
    y_predict_val = {}
    y_predict_test = []
    train_error = {}
    val_error = {}
    test_error = []
    MSE_train = {}
    MSE_val = {}
    
    for i in range(num_series):
        myresults_train = sio.loadmat('myresults_train' + str(i+1) + '.mat')
        y_predict_train[i+1] = myresults_train['prediction']
        train_error[i+1] = myresults_train['error']
        MSE_train[i+1] = myresults_train['MSE']
        
        if train_ratio < 1:
            myresults_val = sio.loadmat('myresults_val' + str(i+1) + '.mat')
            y_predict_val[i+1] = myresults_val['prediction_val']
            val_error[i+1] = myresults_val['error_val']
            MSE_val[i+1] = myresults_val['MSE_val']            
        else:
            MSE_val = None
            val_error = None
            y_predict_val = None
        
    '''Prediction for testing data is done already if y_test is not none'''
    if test:
        y_real_test = y_test.transpose()
        myresults_test = sio.loadmat('myresults_test.mat')
        y_predict_test= myresults_test['prediction_test']
        test_error = myresults_test['error_test']
        MSE_test = myresults_test['MSE_test']            
    else:
        MSE_test = None
        test_error = None
        y_predict_test = None   
        
    

    
    #plot the prediction results
    if plot: 
        import matplotlib
        cmap = matplotlib.cm.get_cmap('Paired')
            
        s=12

        #plot the prediction vs real
        for i in range(steps):
            for j in range(m_y):
                
                for index in range(num_series):
                    plt.figure(figsize=(5,3))
                    plt.plot(y_real_train[index+1][j], color= cmap(j*2+1), label= 'real')
                    plt.plot(y_predict_train[index+1][m_y*i+j], '--', color= 'xkcd:coral', label = 'prediction')
                    plt.title('Training data' + str(i+1) +'-step prediction for y' + str(j+1),fontsize=s)
                    plt.xlabel('Time index',fontsize=s)
                    plt.ylabel('y',fontsize=s)
                    plt.legend(fontsize=s)
                    plt.tight_layout()                    
                    plt.savefig('Train_var_' + str(j+1)+'_step_'+str(i+1)+ '_series_' + str(index+1) +'.png', dpi = 600,bbox_inches='tight')
                    
                    if train_ratio < 1:
                        plt.figure(figsize=(5,3))
                        plt.plot(y_real_val[index+1][j], color= cmap(j*2+1), label= 'real')
                        plt.plot(y_predict_val[index+1][m_y*i+j], '--', color= 'xkcd:coral',label = 'prediction')
                        plt.title('Validation data ' + str(i+1) +'-step prediction for y' + str(j+1),fontsize=s)
                        plt.xlabel('Time index',fontsize=s)
                        plt.ylabel('y',fontsize=s)
                        plt.legend(fontsize=s)
                        plt.tight_layout()                    
                        plt.savefig('Val_var_' + str(j+1)+'_step_'+str(i+1)+ '_series_' + str(index+1) + '.png', dpi = 600,bbox_inches='tight')

                if test:
                    plt.figure(figsize=(5,3))
                    plt.plot(y_real_test[j], color= cmap(j*2+1), label= 'real')
                    plt.plot(y_predict_test[m_y*i+j], '--',color= 'xkcd:coral', label = 'prediction')
                    plt.title('Test data ' + str(i+1) +'-step prediction for y' + str(j+1),fontsize=s)
                    plt.xlabel('Time index',fontsize=s)
                    plt.ylabel('y',fontsize=s)
                    plt.legend(fontsize=s)
                    plt.tight_layout()                    
                    plt.savefig('Test_var_' + str(j+1)+'_step_'+str(i+1)+'.png', dpi = 600,bbox_inches='tight')

                
                plt.close('all')
        
        #plot fitting errors
        for index in range(num_series):
            max_limit=np.nanmax(train_error[index+1][-m_y:],axis=1)
            min_limit=np.nanmin(train_error[index+1][-m_y:],axis=1)
            
            fig, axs = plt.subplots(steps,m_y, figsize=(3*m_y,2*steps))
            
            if m_y >1:
                for i in range(steps):
                    for j in range(m_y):
                        axs[i,j].plot(train_error[index+1][m_y*i+j], color= cmap(j*2+1))
                        axs[i,j].set_title('Training data ' + str(i+1) +'-step error for y' + str(j+1), fontsize=s)
                        axs[i,j].set_ylim(min_limit[j]-abs(min_limit[j])*0.5,max_limit[j]*1.5)
                        if i is steps-1:
                            axs[i,j].set_xlabel('Time index', fontsize=s)              
                fig.tight_layout()
                plt.savefig('Train error series ' + str(index+1) +'.png', dpi = 600,bbox_inches='tight')
            else:
                for i in range(steps):
                    axs[i].plot(train_error[index+1][i], color= cmap(1))
                    axs[i].set_title('Training data ' + str(i+1) +'-step error for y' + str(1), fontsize=s)
                    axs[i].set_ylim(min_limit-abs(min_limit)*0.5,max_limit*1.5)
                    if i is steps-1:
                        axs[i].set_xlabel('Time index', fontsize=s)              
                fig.tight_layout()
                plt.savefig('Train error series ' + str(index+1) +'.png', dpi = 600,bbox_inches='tight')
            
            
            if train_ratio < 1: 
                
                max_limit=np.nanmax(val_error[index+1][-m_y:],axis=1)
                min_limit=np.nanmin(val_error[index+1][-m_y:],axis=1)
                fig1, axs1 = plt.subplots(steps,m_y, figsize=(3*m_y,2*steps))
                
                if m_y >1:
                    for i in range(steps):
                        for j in range(m_y):
                            axs1[i,j].plot(val_error[index+1][m_y*i+j], color= cmap(j*2+1))
                            axs1[i,j].set_title('Val data ' + str(i+1) +'-step error for y' + str(j+1), fontsize=s)
                            axs1[i,j].set_ylim(min_limit[j]-abs(min_limit[j])*0.5,max_limit[j]*1.5)
                            if i is steps-1:
                                axs1[i,j].set_xlabel('Time index', fontsize=s)                
                    fig1.tight_layout()
                    plt.savefig('Val error series ' + str(index+1) +'.png', dpi=600,bbox_inches='tight')
                else:
                    for i in range(steps):
                        axs1[i].plot(val_error[index+1][i], color= cmap(1))
                        axs1[i].set_title('Val data ' + str(i+1) +'-step error for y' + str(1), fontsize=s)
                        axs1[i].set_ylim(min_limit-abs(min_limit)*0.5,max_limit*1.5)
                        if i is steps-1:
                            axs1[i].set_xlabel('Time index', fontsize=s)                
                    fig1.tight_layout()
                    plt.savefig('Val error series ' + str(index+1) +'.png', dpi=600,bbox_inches='tight')            
            
        if test:  
            max_limit=np.nanmax(test_error[-m_y:],axis=1)
            min_limit=np.nanmin(test_error[-m_y:],axis=1)
            fig2, axs2 = plt.subplots(steps,m_y, figsize=(3*m_y,2*steps))
            
            if m_y>1:
                for i in range(steps):
                    for j in range(m_y):
                        axs2[i,j].plot(test_error[m_y*i+j], color= cmap(j*2+1))
                        axs2[i,j].set_title('Test data ' + str(i+1) +'-step error for y' + str(j+1), fontsize=s)
                        axs2[i,j].set_ylim(min_limit[j]-abs(min_limit[j]*0.5),max_limit[j]*1.5)
                        if i is steps-1:
                            axs2[i,j].set_xlabel('Time index', fontsize=s)                
                fig2.tight_layout()
                plt.savefig('Test error.png', dpi=600,bbox_inches='tight')        
            else:
                for i in range(steps):
                    axs2[i].plot(test_error[i], color= cmap(1))
                    axs2[i].set_title('Test data ' + str(i+1) +'-step error for y' + str(1), fontsize=s)
                    axs2[i].set_ylim(min_limit-abs(min_limit)*0.5,max_limit*1.5)
                    if i is steps-1:
                        axs2[i].set_xlabel('Time index', fontsize=s)                
                fig2.tight_layout()
                plt.savefig('Test error.png', dpi=600,bbox_inches='tight')        
        
        
        #MSE for prediction results over different steps
        for index in range(num_series):
            for i in range(m_y):
                plt.figure(figsize=(3,2))
                plt.plot(MSE_train[index+1][i], 'd-', color = cmap(i*2+1))
                plt.title('MSE for y' + str(i+1) +' training prediction', fontsize = s)
                plt.xlabel('k-step ahead', fontsize = s)
                plt.ylabel('MSE', fontsize = s)
                plt.tight_layout()                    
                plt.savefig('MSE_train '+str(i+1)+ ' series '+ str(index+1)+'.png', dpi=600,bbox_inches='tight')        
        
            if train_ratio < 1: 
                for i in range(m_y):
                    plt.figure(figsize=(3,2))
                    plt.plot(MSE_val[index+1][i], 'd-', color = cmap(i*2+1))
                    plt.title('MSE for y' + str(i+1) +' validation prediction', fontsize = s)
                    plt.xlabel('k-step ahead', fontsize = s)
                    plt.ylabel('MSE', fontsize = s)
                    plt.tight_layout()                    
                    plt.savefig('MSE_val '+str(i+1) + ' series '+ str(index+1)+'.png', dpi=600,bbox_inches='tight')  

                
        if test:
            for i in range(m_y):
                plt.figure(figsize=(3,2))
                plt.plot(MSE_test[i], 'd-', color = cmap(i*2+1))
                plt.title('MSE for y' + str(i+1) +' testing prediction', fontsize = s)
                plt.xlabel('k-step ahead', fontsize = s)
                plt.ylabel('MSE', fontsize = s)
                plt.tight_layout()                    
                plt.savefig('MSE_test'+str(i+1)+'.png', dpi=600,bbox_inches='tight')

    myresults = sio.loadmat('my_matlab_ss')
    optimal_params = {}
    optimal_params['ord'] = myresults['final_order']
    optimal_params['method'] = myresults['final_model']

        
        
    return(optimal_params, myresults, MSE_train, MSE_val, MSE_test, y_predict_train, y_predict_val, y_predict_test, train_error, val_error, test_error)
    
    
    
    




def timeseries_matlab_prediction(X, y, X_scale=None, y_scale=None,  mysys='my_matlab_ss', steps = 3, index = 0, plot = True):
    
    '''This function used the fitted model by using the fitted system by matlab n4sid
    Input:
        X: dictionary of training data predictors numpy array: Nxm, composed of all the data (several time seireses)
        y: dictionary of training data response numy array: Nx1, composed of all the data (several time seireses)
        X_scale: data used to scale X
        y_scale: data used to scale y
        sys: the name of the system, the exact sys in this matfile should be named as sys
        steps: number of steps considered for prediction
        index: saved as kstep(index).mat file
        plot: flag for plotting results or not, default TRUE
        
        
    Output:
        Preditction results:
            MSE_test with differnt prediction steps
            y_predict_test: prediction by final optimal model, Num_steps X timeinstances, the frist row is one step ahead by Kalman
            error: the error _predict_test-y_real
    '''
    
    #scale data
    if X_scale is not None:
        scaler = StandardScaler()
        scaler.fit(X_scale)
        X = scaler.transform(X)
            
        scalery = StandardScaler()
        scalery.fit(y_scale)
        y=scalery.transform(y)
    
    
    #save data and params
    sio.savemat('myparams_prediction.mat', {'steps':steps, 'id':index, 'mydimy':np.shape(y)[1], 'mysys': mysys})
                 
    mydata_prediction = np.vstack((np.transpose(y),np.transpose(X)))
    sio.savemat('mydata_prediction.mat', {'mydata_prediction':mydata_prediction})

    
    ##load matlab
    eng = matlab.engine.start_matlab()
    eng.cd(os.getcwd())
    #eng.addpath(url, nargout=0)
    eng.Matlab_prediction(nargout=0)
    
    eng.quit()
    
    
    
    #load results
    prediction_test = sio.loadmat('kstep' + str(index) +'.mat')
    y_real_test = y.transpose()
    y_predict_test = np.array(prediction_test['prediction'])
    test_error = np.array(prediction_test['error'])    
    MSE_test = np.array(prediction_test['MSE'])
    
    m_y = np.shape(y)[1]
    
    #plot results
    if plot: 
        import matplotlib
        cmap = matplotlib.cm.get_cmap('Paired')
            
        s=12

        #plot the prediction vs real
        for i in range(steps):
            for j in range(m_y):
                plt.figure(figsize=(5,3))
                plt.plot(y_real_test[j], color= cmap(j*2+1), label= 'real')
                plt.plot(y_predict_test[m_y*i+j], '--',color= 'xkcd:coral', label = 'prediction')
                plt.title('Test data ' + str(i+1) +'-step prediction for y' + str(j+1),fontsize=s)
                plt.xlabel('Time index',fontsize=s)
                plt.ylabel('y',fontsize=s)
                plt.legend(fontsize=s)
                plt.tight_layout()                    
                plt.savefig('Test_var_' + str(j+1)+'_step_'+str(i+1)+ '_index_' + str(index)+'.png', dpi = 600,bbox_inches='tight')

                
                plt.close('all')
        
        #plot fitting errors
        max_limit=np.nanmax(test_error[-m_y:],axis=1)
        min_limit=np.nanmin(test_error[-m_y:],axis=1)
        fig2, axs2 = plt.subplots(steps,m_y, figsize=(3*m_y,2*steps))
        
        if m_y >1:
            for i in range(steps):
                for j in range(m_y):
                    axs2[i,j].plot(test_error[m_y*i+j], color= cmap(j*2+1))
                    axs2[i,j].set_title('Test data ' + str(i+1) +'-step error for y' + str(j+1), fontsize=s)
                    axs2[i,j].set_ylim(min_limit[j]-abs(min_limit[j])*0.5,max_limit[j]*1.5)
                    if i is steps-1:
                        axs2[i,j].set_xlabel('Time index', fontsize=s)                
            fig2.tight_layout()
            plt.savefig('Test error ' + str(index) +'.png', dpi=600,bbox_inches='tight')        
        else:
            for i in range(steps):
                axs2[i].plot(test_error[m_y*i], color= cmap(1))
                axs2[i].set_title('Test data ' + str(i+1) +'-step error for y' + str(1), fontsize=s)
                axs2[i].set_ylim(min_limit-abs(min_limit)*0.5,max_limit*1.5)
                if i is steps-1:
                    axs2[i].set_xlabel('Time index', fontsize=s)                
            fig2.tight_layout()
            plt.savefig('Test error ' + str(index) +'.png', dpi=600,bbox_inches='tight')      
        
        #MSE for prediction results over different steps
        for i in range(m_y):
            plt.figure(figsize=(3,2))
            plt.plot(MSE_test[i], 'd-', color = cmap(i*2+1))
            plt.title('MSE for y' + str(i+1) +' testing prediction', fontsize = s)
            plt.xlabel('k-step ahead', fontsize = s)
            plt.ylabel('MSE', fontsize = s)
            plt.tight_layout()                    
            plt.savefig('MSE_test_var_'+str(i+1)+'_index_'+str(index)+'.png', dpi=600,bbox_inches='tight')
       
        
        
        
    return(MSE_test,  y_predict_test, test_error)
    
