# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

##################################################
# import modules

import os
import glob
import pandas as pd

##################################################
# set working direcoty

cwd = os.getcwd()
print(cwd)

path = cwd + '/data/elementarySchool'
file_list = glob.glob(os.path.join(path, "*.csv"))
for file in file_list:
    file_name = os.path.basename(file)
    print(file_name)

# 아래 파일은 성별에 따른 학생수 정보가 부재
# student2022 = pd.read_csv(file_list[9])
# print(student2022.head())
# colList = student2022.columns
# for col in colList:
#     print(col)

# use 2022ElementarySchool.csv
student2022 = pd.read_csv(file_list[4])
print(student2022.head())
colList = student2022.columns
for col in colList:
    print(col)
