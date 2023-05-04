##################################################
# import modules

import os
import pandas as pd
import requests
# from tqdm import tqdm
import geopandas as gpd
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
from pyproj import CRS
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns


# Set the max_columns option to None
pd.set_option('display.max_columns', None)


##################################################
# set working direcoty

cwd = os.getcwd()
# print(cwd)

base_path = "/Users/USER/PycharmProjects/genderSortingAcrossElementarySchoolInKorea"
path_engineered_data = os.path.join(base_path, r'engineered_data')

if not os.path.exists(path_engineered_data):
   os.makedirs(path_engineered_data)

'''
##################################################
# open files

file_name = "data/elementarySchool/2022ElementarySchool.csv"
file_path = os.path.join(base_path, file_name)
ElementarySchoolStudentInfo2022 = pd.read_csv(file_path, encoding='utf-8')
for col in ElementarySchoolStudentInfo2022 .columns:
    print(col)
# print(ElementarySchoolStudentInfo2022['시도교육청'].unique())
ElementarySchoolStudentInfo2022_subset = ElementarySchoolStudentInfo2022[ElementarySchoolStudentInfo2022['시도교육청'].str.contains('서울특별시교육청')]


file_name = "data/elementarySchool/2022년도_학교기본정보(초등).csv"
file_path = os.path.join(base_path, file_name)
ElementarySchoolInfo2022 = pd.read_csv(file_name, encoding='utf-8')
ElementarySchoolInfo2022_subset = ElementarySchoolInfo2022[ElementarySchoolInfo2022['시도교육청'].str.contains('서울특별시교육청')]


##################################################
# merge two data sets

merged_df = pd.merge(ElementarySchoolStudentInfo2022_subset, ElementarySchoolInfo2022_subset, on='정보공시 학교코드', how='inner', indicator=True, suffixes=('', '_new'))
merged_df = merged_df[merged_df.columns.drop(list(merged_df.filter(regex='_new')))]


##################################################
# add coordinate info

# correct the incorrect addresses
merged_df.loc[merged_df['학교명'] == '서울등양초등학교', '학교도로명 주소'] = '서울특별시 강서구 강서로56나길 140'
merged_df.loc[merged_df['학교명'] == '서울미아초등학교', '학교도로명 주소'] = '서울특별시 성북구 삼양로 77'
merged_df.loc[merged_df['학교명'] == '서울언주초등학교', '학교도로명 주소'] = '서울특별시 강남구 남부순환로363길 19'
merged_df.loc[merged_df['학교명'] == '서울수서초등학교', '학교도로명 주소'] = '서울특별시 강남구 광평로51길 46'
merged_df.loc[merged_df['학교명'] == '서울우면초등학교', '학교도로명 주소'] = '서울특별시 서초구 태봉로 59'
merged_df.loc[merged_df['학교명'] == '서울신남초등학교', '학교도로명 주소'] = '서울특별시 양천구 신월동 587'
merged_df.loc[merged_df['학교명'] == '서울장평초등학교', '학교도로명 주소'] = '서울특별시 동대문구 답십리로69길 27'


# NAVER Cloud info
# Replace with your own Naver Cloud API client ID and secret key
CLIENT_ID = ''
CLIENT_SECRET = ''

# Function to get the coordinates for a given address
def get_coordinate(address):
    headers = {'X-NCP-APIGW-API-KEY-ID': CLIENT_ID, 'X-NCP-APIGW-API-KEY': CLIENT_SECRET}
    url = f'https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={address}'
    response = requests.get(url, headers=headers)
    data = response.json()
    if data['status'] == 'OK' and len(data['addresses']) > 0:
        # print ("[%s] Url Request Success" % datetime.datetime.now())
        longitude = data['addresses'][0]['x']
        latitude = data['addresses'][0]['y']
        return longitude, latitude
    else:
        return None, None


# Get the coordinates for each address using the get_coordinate function
merged_df['longitude'], merged_df['latitude'] = zip(*merged_df['학교도로명 주소'].apply(get_coordinate))


# Save the updated DataFrame to a new CSV file
# tqdm.pandas()

file_path = os.path.join(base_path + '/engineered_data', 'merged_df_with_coordinates.csv')
merged_df.to_csv(file_path, index=False, encoding='utf-8')
# merged_df.to_csv('merged_df_with_coordinates.csv', index=False, encoding='cp949')


##################################################
# read school district shp file

file_name = "data/elementarySchooldistrict/초등학교통학구역.shp"
file_path = os.path.join(base_path, file_name)
shapefile = gpd.read_file(file_path)
# print(shapefile.columns)

columns_to_drop = ['CRE_DT', 'UPD_DT', 'BASE_DT']
shapefile_subset = shapefile.drop(columns_to_drop, axis=1)
print(shapefile_subset.columns)
subset = shapefile_subset[shapefile_subset['EDU_UP_NM'] == "서울특별시교육청"]


##################################################
# merge shapefile with point data set(merged_df, or "merged_df_with_coordinates.csv")
merged_df_with_coordinates = merged_df

# convert merged_df_with_coordinates to a GeoDataFrame
points = gpd.GeoDataFrame(merged_df_with_coordinates,
                          geometry=gpd.points_from_xy(merged_df_with_coordinates.longitude,
                                                      merged_df_with_coordinates.latitude))

# infer CRS from latitude and longitude columns using pyproj
points.crs = CRS.from_user_input('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs').to_wkt()

# convert subset to a GeoDataFrame
polygons = gpd.GeoDataFrame(subset)

# reproject points to match the CRS of polygons
points = points.to_crs(polygons.crs)

# perform spatial join
joined = gpd.sjoin(points, polygons, op='within')


##################################################
# plot points and polygon (simple overlay)

fig, ax = plt.subplots(figsize=(10,10))

polygons.plot(ax=ax, alpha=0.5, edgecolor='black')
joined.plot(ax=ax, color='red', markersize=5)

plt.show()


# count the number of points for each polygon
counts = joined.index.value_counts()

# select polygons with more than one point
multi_point_polygons = counts[counts > 1].index.tolist()

# print the list of polygons with more than one point
print(multi_point_polygons)


##################################################
# fill polygons using points info

# check crs of points and polygons
print(points.crs)
print(polygons.crs)

# adjust crs for spatial join
new_crs = polygons.crs
gdf = points.to_crs(new_crs)

# spatial join using subset(shape file of school district)
map_df = subset
joined_df = gpd.sjoin(map_df, gdf, how='inner', op='contains')

# save as shp file
# file_path = os.path.join(base_path + '/engineered_data', 'elementarySchoolGenderSorting.shp')
# joined_df.to_file(file_path)

# save as geojson file
# file_path = os.path.join(base_path + '/engineered_data', "elementarySchoolInfoForVisualization.geojson")
# joined_df.to_file(file_path, driver='GeoJSON')

##################################################
# fill polygons using point info: using number of boys in the first grade

fig, ax = plt.subplots(figsize=(10, 10))
joined_df.plot(column='1학년(남)', cmap='Blues', ax=ax, legend=True)
plt.show()


# generate boys/ratio info of each grade
grades = ['1학년', '2학년', '3학년', '4학년', '5학년', '6학년']

for grade in grades:
    total_column = f"{grade}(합계)"
    columns_to_sum = [f"{grade}(남)", f"{grade}(여)"]
    joined_df[total_column] = joined_df[columns_to_sum].sum(axis=1)

grades = ['1학년', '2학년', '3학년', '4학년', '5학년', '6학년']
genders = ['남']

for grade in grades:
    for gender in genders:
        column_name = f"{grade}({gender})"
        column_name_denominator = f"{grade}(합계)"
        joined_df[column_name + '비율'] = joined_df[column_name]/joined_df[column_name_denominator]

columns = joined_df.columns
for column in columns:
  print(column)


# # plot boys ratio
# fig, ax = plt.subplots(figsize=(10, 10))
# joined_df.plot(column='1학년(남)비율', cmap='Blues', ax=ax, legend=True)
# plt.show()

# # set title and axis labels
# ax.set_title('1학년(남) 비율', fontdict={'fontsize': 20})
# ax.set_axis_off()

# # save the figure as a PNG image
# plt.savefig('map.png', dpi=300)
'''

##################################################
# open files

file_name = "engineered_data/merged_df_with_coordinates.csv"
file_path = os.path.join(base_path, file_name)
ElementarySchool2022 = pd.read_csv(file_path, encoding='utf-8')


##################################################
# read school district shp file

file_name = "data/elementarySchooldistrict/초등학교통학구역.shp"
file_path = os.path.join(base_path, file_name)
shapefile = gpd.read_file(file_path)
# print(shapefile.columns)

columns_to_drop = ['CRE_DT', 'UPD_DT', 'BASE_DT']
shapefile_subset = shapefile.drop(columns_to_drop, axis=1)
print(shapefile_subset.columns)
subset = shapefile_subset[shapefile_subset['EDU_UP_NM'] == "서울특별시교육청"]


##################################################
# merge shapefile with point data set(merged_df, or "merged_df_with_coordinates.csv")
merged_df_with_coordinates = ElementarySchool2022

# convert merged_df_with_coordinates to a GeoDataFrame
points = gpd.GeoDataFrame(merged_df_with_coordinates,
                          geometry=gpd.points_from_xy(merged_df_with_coordinates.longitude,
                                                      merged_df_with_coordinates.latitude))

# infer CRS from latitude and longitude columns using pyproj
points.crs = CRS.from_user_input('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs').to_wkt()

# convert subset to a GeoDataFrame
polygons = gpd.GeoDataFrame(subset)

# reproject points to match the CRS of polygons
points = points.to_crs(polygons.crs)

# perform spatial join
joined = gpd.sjoin(points, polygons, op='within')


# check crs of points and polygons
print(points.crs)
print(polygons.crs)

# adjust crs for spatial join
new_crs = polygons.crs
gdf = points.to_crs(new_crs)

# spatial join using subset(shape file of school district)
map_df = subset
joined_df = gpd.sjoin(map_df, gdf, how='inner', op='contains')


##################################################
# # plot points and polygon (simple overlay)
# fig, ax = plt.subplots(figsize=(10,10))
#
# polygons.plot(ax=ax, alpha=0.5, edgecolor='black')
# joined.plot(ax=ax, color='red', markersize=5)
#
# plt.show()

# count the number of points for each polygon
counts = joined.index.value_counts()

# select polygons with more than one point
multi_point_polygons = counts[counts > 1].index.tolist()

# print the list of polygons with more than one point
print(multi_point_polygons)

# generate boys/ratio info of each grade
grades = ['1학년', '2학년', '3학년', '4학년', '5학년', '6학년']

for grade in grades:
    total_column = f"{grade}(합계)"
    columns_to_sum = [f"{grade}(남)", f"{grade}(여)"]
    joined_df[total_column] = joined_df[columns_to_sum].sum(axis=1)

grades = ['1학년', '2학년', '3학년', '4학년', '5학년', '6학년']
genders = ['남']

for grade in grades:
    for gender in genders:
        column_name = f"{grade}({gender})"
        column_name_denominator = f"{grade}(합계)"
        joined_df[column_name + '비율'] = joined_df[column_name]/joined_df[column_name_denominator]

# # plot boys ratio
# fig, ax = plt.subplots(figsize=(10, 10))
# joined_df.plot(column='1학년(남)비율', cmap='Blues', ax=ax, legend=True)
# plt.show()

# for grade in grades:
#     for gender in genders:
#         plot_name = f"{grade}(남)비율"
#         fig, ax = plt.subplots(figsize=(10, 10))
#         joined_df.plot(column=plot_name, cmap='Blues', ax=ax, legend=True)
#         plt.savefig(f'{plot_name}.png', dpi=300)

# # create a custom colormap
# cmap = LinearSegmentedColormap.from_list('custom', [(0, 'red'), (0.5, 'white'), (1, 'blue')])
#
# # loop through grades and genders and plot the data
# for grade in grades:
#     for gender in genders:
#         plot_name = f"{grade}({gender})비율"
#         fig, ax = plt.subplots(figsize=(10, 10))
#         vmin, vmax = joined_df[plot_name].min(), joined_df[plot_name].max()
#         norm = plt.Normalize(vmin=vmin, vmax=vmax)
#         joined_df.plot(column=plot_name, cmap=cmap, ax=ax, norm=norm, legend=True)
#         plt.savefig(f'{plot_name}.png', dpi=100)


# sns.set_theme(style="whitegrid")
# sns.histplot(data=joined_df, x="1학년(남)비율", kde=True)
#
# # create the plot
# fig, ax = plt.subplots()
# ax.hist(joined_df["1학년(남)비율"], bins=30, density=True)
#
# # set labels and title
# ax.set_xlabel('Value')
# ax.set_ylabel('Density')
# ax.set_title('Normal Distribution')
#
# # save the plot to a file
# plt.savefig('distribution.png', dpi=100)

# Set the font family to one that supports Hangul characters
plt.rcParams['font.family'] = 'NanumGothic'

sns.set_style("whitegrid")

# create sample data
data = sns.load_dataset("tips")

# create distribution plot
sns.kdeplot(data=joined_df["1학년(남)비율"], fill=True)

# add histogram line
sns.histplot(data=joined_df["1학년(남)비율"], color="grey", alpha=.2, kde=True)

# save plot
plt.savefig("distribution_plot_with_histogram.png", dpi=300)



# create histogram plot
fig, ax = plt.subplots(figsize=(8, 5))
sns.histplot(data=joined_df["1학년(남)비율"], ax=ax, color="grey", alpha=.2, kde=True)

# add KDE plot on twin Axes
ax2 = ax.twinx()
sns.kdeplot(data=joined_df["1학년(남)비율"], shade=True, ax=ax2, color='red')
ax2.set_ylabel('KDE', color='red')
ax2.tick_params(axis='y', labelcolor='red')
plt.show()