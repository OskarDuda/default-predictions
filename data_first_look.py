"""
Created on 14.07.18, 22:15 
author: oskar 
"""

###########
##Imports##
###########

#Basic libraries
import pandas as pd
import numpy as np
import time

#Plotting libraries
import seaborn as sns
import matplotlib.pyplot as plt

#ML
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import KNeighborsRegressor
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import BaggingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.ensemble import AdaBoostClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.preprocessing import LabelBinarizer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier

#System
from os import path

########################
##Function definitions##
########################
def is_default(line):
    values_perceived_as_default = ['Charged Off',
                                   'Default',
                                   'Does not meet the credit policy. Status:Charged Off',
                                   'Late (31-120 days)']

    return line['loan_status'] in values_perceived_as_default


def group_title_column(line):
    values_preserved = ['Debt consolidation',
                        'Credit card refinancing',
                        'Home improvement',
                        'Other',
                        'Debt Consolidation',
                        'Major purchase']

    if line['title'] not in values_preserved:
        return 'Other'
    else:
        return line['title']


def numerate_pymnt_d(value):
    translator = dict(zip(['Jan',
                  'Feb',
                  'Mar',
                  'Apr',
                  'May',
                  'Jun',
                  'Jul',
                  'Aug',
                  'Sep',
                  'Oct',
                  'Nov',
                  'Dec'],
                  range(1,13)))
    if pd.isnull(value):
        return value
    else:
        return translator[value[:3]] + 12*int(value[-4:])


def numerate_emp_length(value):
    if value == '< 1 year':
        return 0
    elif value == '10+ years':
        return 10
    elif pd.isnull(value):
        return np.nan
    else:
        return int(value.split()[0])


def input_values(X, y, model=None):
    if model:
        clf = model
    else:
        clf = KNeighborsRegressor(n_neighbors=100)

    no_nan_indeces = y.dropna().index
    nan_indeces = y[y.isna()].index

    clf.fit(X.loc[no_nan_indeces],
            y[no_nan_indeces])

    inputed_values = clf.predict(X.loc[nan_indeces])

    return inputed_values



print("Start time: ", time.asctime())
#########################
##Step 1: Load the data##
#########################
directory = r"C:\Users\duos8001\Documents\Python\Machine Learning tutorial\Default Prediction\Data"
filename = 'loan.csv'
full_path = path.join(directory, filename)
n = 300000
if n:
    raw_df = pd.read_csv(full_path).sample(n=n)
else:
    raw_df = pd.read_csv(full_path)
df = raw_df.copy()
print("Data loaded. Number of entries: ", len(raw_df))

###############################
##Step 2: Preprocess the data##
###############################
# accepted_nans_per_column = 0.01
# criteria = df.isna().sum() < len(df) * accepted_nans_per_column
# df = df[criteria.index[criteria]]

df['is_default'] = df.apply(is_default, axis=1)
df['title'] = df.apply(group_title_column, axis=1)
df['emp_length'] = df['emp_length'].apply(numerate_emp_length)
df['last_pymnt_d'] = df['last_pymnt_d'].apply(numerate_pymnt_d)
df['next_pymnt_d'] = df['next_pymnt_d'].apply(numerate_pymnt_d)
not_nan_idx = df['emp_title'].dropna().index
df['emp_title'][not_nan_idx] = df['emp_title'][not_nan_idx].apply(lambda x: x.lower())
df['emp_title'].fillna('other', inplace=True)
corrs = df.corr()

input_by = ['member_id', 'out_prncp_inv']
X = df[input_by]
to_input = df['last_pymnt_d']
nan_indeces = df[df['last_pymnt_d'].isnull()].index
df['last_pymnt_d'][nan_indeces] = input_values(df[input_by],
                                               to_input)
input_by = ['last_pymnt_d']
X = df[input_by]
to_input = df['next_pymnt_d']
nan_indeces = df[df['next_pymnt_d'].isnull()].index
df['last_pymnt_d'][nan_indeces] = input_values(df[input_by],
                                               to_input,
                                               LinearRegression())
input_by = ['revol_bal']
useful_idx = df[input_by].dropna().index
to_input = df['total_rev_hi_lim'][useful_idx]
nan_indeces = df.loc[useful_idx][df['total_rev_hi_lim'][useful_idx].isnull()].index
df['total_rev_hi_lim'][nan_indeces] = input_values(df[input_by].loc[useful_idx],
                                                   to_input,
                                             LinearRegression())

input_by = ['annual_inc', 'revol_bal', 'total_rev_hi_lim','funded_amnt_inv']
useful_idx = df[input_by].dropna().index
to_input = df['tot_cur_bal'][useful_idx]
nan_indeces = df.loc[useful_idx][df['tot_cur_bal'][useful_idx].isnull()].index
df['tot_cur_bal'][nan_indeces] = input_values(df[input_by].loc[useful_idx],
                                             to_input)


input_by = ['funded_amnt_inv', 'loan_amnt', 'funded_amnt', 'total_acc', 'funded_amnt']
useful_idx = df[input_by].dropna().index
to_input = df['emp_length'][useful_idx]
nan_indeces = df.loc[useful_idx][df['emp_length'][useful_idx].isnull()].index
df['emp_length'][nan_indeces] = input_values(df[input_by].loc[useful_idx],
                                             to_input)

df.drop(labels = df[df.revol_util.isnull()].index, inplace=True)
df = df.dropna(axis=1)

encoder = LabelEncoder()
y = df['is_default']
X = df.drop(['is_default', 'loan_status'], axis=1)
for col in X.columns:
    encoder.fit(X[col])
    X[col] = encoder.transform(X[col])

binarizer = LabelBinarizer()
cols_to_binarize = [x for x in X.columns if len(X[x].value_counts())<10]
for col in cols_to_binarize:
    binarizer.fit(X[col])
    binned_names = [col + '_' + str(x) for x in binarizer.classes_]
    binned_values = np.transpose(binarizer.transform(X[col]))
    d = dict(zip(binned_names, binned_values))
    X = X.assign(**d)
    X.drop(col, inplace = True, axis = 1)


print("Data transformed")

####################
##Step 3: Plotting##
####################
# plt.cla()
# sns.pairplot(X[X.columns[11:21]].join(y), hue = 'is_default')
# sns.heatmap(df[df.columns[:11]].isna())
# plt.show()





##########################
##Step 4: Training model##
##########################
model_selector = 'rand_forest'
reductor_selector = 'none'
seed = 17

models = {'rand_forest' : RandomForestClassifier(n_estimators=500, verbose=2, max_depth=4, max_features=50, random_state=seed),
          'boosted_trees' : GradientBoostingClassifier(n_estimators=1600, verbose=2, max_features=40, subsample=0.5, random_state=seed)}
model = models.get(model_selector)
reductors = {'pca' : PCA(n_components=len(X.columns), random_state=seed),
             'lda' : LinearDiscriminantAnalysis(n_components=len(X.columns), random_state=seed),
             'none' : None}
red = reductors.get(reductor_selector)

if red:
    print("Feature space transformation")
    red.fit(X,y)
    X_r = red.transform(X)
    X_train, X_test, y_train, y_test = train_test_split(X_r, y, test_size=0.05, random_state=seed)
    msg = lambda x: "Accuracy of trained model with feature space transformation is {:.4f}%".format(100*x)
else:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.05, random_state=seed)
    msg = lambda x: "Accuracy of trained model without feature space transformation is {:.4f}%".format(100 * x)


print("Training the model")
model.fit(X_train, y_train)
score = model.score(X_test, y_test)
print(msg(score))
