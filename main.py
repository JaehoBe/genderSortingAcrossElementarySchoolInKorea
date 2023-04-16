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
import geopandas as gpd
import matplotlib.pyplot as plt

# Set the max_columns option to None
pd.set_option('display.max_columns', None)

##################################################
# set working direcoty

cwd = os.getcwd()
# print(cwd)

base_path = "/Users/jaehojung/PycharmProjects/genderSortingAcrossElementarySchoolInKorea"


##################################################
# read elementary school data file

file_name = "data/elementarySchool/2022ElementarySchool.csv"
file_path = os.path.join(base_path, file_name)
studentInfo2022 = pd.read_csv(file_path)
# print(studentInfo2022)
# for col in studentInfo2022.columns:
#     print(col)
# print(studentInfo2022['정보공시 학교코드'].head())
# print(studentInfo2022['시도교육청'].unique())
studentInfo2022_subset = studentInfo2022[studentInfo2022['시도교육청'].str.contains('서울특별시교육청')]

# ##################################################
# read elementary school info file
# source: https://schoolinfo.go.kr/ng/go/pnnggo_a01_l2.do 학교기본정보

file_name = "data/elementarySchool/2022년도_학교기본정보(초등).csv"
file_path = os.path.join(base_path, file_name)
schoolInfo2022 = pd.read_csv(file_path)
print(schoolInfo2022.head())
for col in schoolInfo2022.columns:
    print(col)
# print(schoolInfo2022['시도교육청'].head())
schoolInfo2022_subset = schoolInfo2022[schoolInfo2022['시도교육청'].str.contains('서울특별시교육청')]

# remove "번지."
schoolInfo2022_subset['상세주소내역'] = schoolInfo2022_subset['상세주소내역'].str.replace('번지.', '')
schoolInfo2022_subset['소재지지번주소'] = schoolInfo2022_subset['주소내역'] + " " + schoolInfo2022_subset['상세주소내역']
# print(schoolInfo2022_subset['소재지지번주소'].head())

# ##################################################
# # read elementary school coordinate info
#
# file_name = "data/elementarySchool/shoolCoordinates_20230322.csv"
# file_path = os.path.join(base_path, file_name)
# schoolCoordinateInfo = pd.read_csv(file_path, encoding='cp949')
# # print(schoolCoordinateInfo.head())
# for col in schoolCoordinateInfo.columns:
#     print(col)
# # print(schoolCoordinateInfo['학교급구분'].unique())
# # print(schoolCoordinateInfo['시도교육청명'].unique())
#
# schoolCoordinateInfo_elementarty = schoolCoordinateInfo[schoolCoordinateInfo['학교급구분'].str.contains('초등학교')]
# schoolCoordinateInfo_subset = schoolCoordinateInfo[schoolCoordinateInfo['시도교육청명'].str.contains('서울특별시교육청')]

##################################################
# combine three data set

merged_df = pd.merge(studentInfo2022_subset, schoolInfo2022_subset, on='정보공시 학교코드', how='inner', indicator=True, suffixes=('', '_new'))
# print(merged_df.head())
# print(merged_df.columns)

file_name = "merged_df.csv"
file_path = os.path.join(base_path, file_name)
merged_df.to_csv(file_path)



# Convert the pandas dataframe to a GeoDataFrame with geometry
geometry = gpd.points_from_xy(merged_df['경도'], merged_df['위도'])
gdf = gpd.GeoDataFrame(merged_df, geometry=geometry)
# Set the CRS of the GeoDataFrame
gdf.crs = "EPSG:5168"

# gdf.to_csv('path/to/your/data.csv', index=False)

##################################################
# read school district shp file

file_name = "data/elementarySchooldistrict/초등학교통학구역.shp"
file_path = os.path.join(base_path, file_name)
shpFile = gpd.read_file(file_path)
# print(shpFile)
# print(shpFile.crs)

# shpFile_Columns = shpFile.columns
# for column in shpFile_Columns:
#     print(column)

columns_to_drop = ['CRE_DT', 'UPD_DT', 'BASE_DT']
shpFile_subset = shpFile.drop(columns_to_drop, axis=1)
# print(shpFile_subset.columns)

gdf = gdf.to_crs(shpFile.crs)

# print(gdf.head())
# print(shpFile_subset.head())

# Perform a spatial join to associate each point with the containing polygon
joined = gpd.sjoin(gdf, shpFile, how='left', op='within')
# print(joined.head())

# # Plot the points in the GeoDataFrame
# fig, ax = plt.subplots()
# ax.set_aspect('equal')
# gdf.plot(ax=ax, markersize=1, color='red')
#
# # Plot the polygons in the shapefile
# fig, ax = plt.subplots()
# ax.set_aspect('equal')
# shpFile.plot(ax=ax, color='blue')
#
# Show the plots
# plt.show()


# merged = shapefile.merge(gdf, on='column_with_common_values', how='left')
# print(merged.head())

