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
from collections import Counter
import re

plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['font.size'] = 12

# Set the max_columns option to None
pd.set_option('display.max_columns', None)


##################################################
# set working directory

cwd = os.getcwd()
# print(cwd)

base_path = "/Users/USER/PycharmProjects/genderSortingAcrossElementarySchoolInKorea"
path_engineered_data = os.path.join(base_path, r'engineered_data')

if not os.path.exists(path_engineered_data):
   os.makedirs(path_engineered_data)


'''
# ##################################################
# number of birth, boy/girl ratio of korea
data = {
    'year': ['2010', '2011', '2012', '2013', '2014',
            '2015', '2016', '2017', '2018', '2019', '2020'],
    'sKoreaBirthTotal': [470171, 471265, 484550, 436455, 435435,
                   438420, 406243, 357771, 326822, 302676, 272337],
    'sKoreaBoyGirlRatio': [106.9, 105.7, 105.7, 105.3, 105.3,
                   105.3, 105.0, 106.3, 105.4, 105.5, 104.8]
}

korean_births_df = pd.DataFrame(data)
print(korean_births_df)

# korean_births_df['sKoreaBoy'] = korean_births_df['sKoreaBoyGirlRatio']/100 * korean_births_df['sKoreaBirthTotal']
# print(korean_births_df['sKoreaBoy'])

# korean_births_df['sKoreaBoyGirlRatio'] = [korean_births_df['sKoreaBoyGirlRatio']/(100 + korean_births_df['sKoreaBoyGirlRatio']) ] * 100
korean_births_df['sKoreaBoyGirlRatio'] = (korean_births_df['numberOfBoys'] / korean_births_df['numberOfGirls']) * 100

print(korean_births_df['sKoreaBoyGirlRatio'])


##################################################
# open files: seoul birth data
file_name = "data/seoulBirthData/출산순위별+출생_20230508155221.csv"
file_path = os.path.join(base_path, file_name)
df = pd.read_csv(file_path, encoding='utf-8', header=[0,1,2])

# print(df.head())

# Split the data into df1 and df2
df1 = df.iloc[:, :2]
df2 = df.iloc[:, 2:]

df2.columns = df2.columns.droplevel(level=1)

# Translate lower level headers
df2 = df2.rename(columns={'계': 'total', '남자': 'male', '여자': 'female'})

df2 = df2.drop(index=0)

# Get the upper header
upper_header = df2.columns.get_level_values(0)

# Get the lower header
lower_header = df2.columns.get_level_values(1)

# Get the year information
year_info = upper_header.str.split(" ").str[0]

# Add the year information to the lower header
new_lower_header = year_info + lower_header

# Assign the new header to the DataFrame
df2.columns = [upper_header, new_lower_header]

# drop upper header
df2.columns = df2.columns.droplevel(0)

# drop the first row
df1 = df1.iloc[1:]

# drop the first column
df1 = df1.iloc[:, 1:]
df1.columns = ['bySeoulDistrict']
df2 = df2.set_index(df1['bySeoulDistrict'])
df2.loc['SeoulTotal'] = df2.sum(axis=0)


total_cols = df2.filter(like='total').columns
df2_total = df2[total_cols]
seoul_total = df2.loc['SeoulTotal', total_cols]

male_cols = df2.filter(regex='^(?!.*female).*male$').columns
df2_male = df2[male_cols]
seoul_male = df2.loc['SeoulTotal', male_cols]

female_cols = df2.filter(like='female').columns
df2_female = df2[female_cols]
seoul_female = df2.loc['SeoulTotal', female_cols]

# reset index of each series
total = seoul_total.reset_index(drop=True)
male = seoul_male.reset_index(drop=True)
female = seoul_female.reset_index(drop=True)

# concatenate horizontally
dfSeoulBirth = pd.concat([total, male, female], axis=1)
dfSeoulBirth['year'] = range(2000, 2022)

dfSeoulBirth.columns = ['SeoulTotal', 'SeoulMaleTotal', 'SeoulFemaleTotal', 'year']

dfSeoulBirth = dfSeoulBirth.reindex(columns=['year', 'SeoulBirthTotal', 'SeoulBirthMale', 'SeoulBirthFemale'])

# convert the "year" column to a string type
dfSeoulBirth['year'] = dfSeoulBirth['year'].astype(str)

# remove the "년" string from the "year" column
dfSeoulBirth['year'] = dfSeoulBirth['year'].str.replace('년', '')

print(dfSeoulBirth)
'''

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
'''

##################################################
# elementary school 
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
file_path = os.path.join(base_path + '/engineered_data', 'merged_df_with_coordinates.csv')
merged_df = pd.read_csv(file_path, encoding='utf-8')
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
counts = joined.groupby('index_right').size()
print(counts)

# print the number of points in each polygon
for index, count in counts.items():
    polygon_name = subsetMiddle.loc[index, 'HAKGUDO_NM']
    print(f"Polygon '{polygon_name}' has {count} points.")


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

# joined_df_columns = joined_df.columns
# for col in joined_df_columns:
#     print(col)

# print(joined_df['설립구분'].unique())
# print(joined_df['학교특성'].unique())
# print(joined_df['설립유형'].unique())
# print(joined_df['주야구분'].unique())

# combinations = list(zip(joined_df['설립구분'], joined_df['설립유형']))
# count = Counter(combinations)
# for combination, num in count.items():
#     print(f"{combination}: {num}")

joined_df['private'] = joined_df['설립구분'].apply(lambda x: 1 if x == '사립' else 0)
joined_df['annexedToSchool'] = joined_df['설립유형'].apply(lambda x: 0 if x == '단설' else 1)

# combinations = list(zip(joined_df['private'], joined_df['annexedToSchool']))
# count = Counter(combinations)
# for combination, num in count.items():
#     print(f"{combination}: {num}")

joined_df = joined_df.drop(columns=['학교급코드', '제외여부', '제외사유', '학교특성', '_merge', '전화번호', '팩스번호'])

# grades = ['1학년', '2학년', '3학년', '4학년', '5학년', '6학년']
# genders = ['남']
#
# boy_cols = [f"{g}(남)" for g in grades]
# girl_cols = [f"{g}(여)" for g in grades]
# boy_ratio = joined_df[boy_cols].describe()
# girl_ratio = joined_df[girl_cols].describe()
#
#
# Define a mapping of Korean column names to English column names
columns_mapping = {
    "OBJECTID": "object_id",
    "HAKGUDO_ID": "hakgudo_id",
    "HAKGUDO_NM": "hakgudo_name",
    "HAKGUDO_GB": "hakgudo_type",
    "SD_CD": "sd_code",
    "SGG_CD": "sgg_code",
    "EDU_UP_CD": "edu_up_code",
    "EDU_UP_NM": "edu_up_name",
    "EDU_CD": "edu_code",
    "EDU_NM": "edu_name",
    "geometry": "geometry",
    "index_right": "index_right",
    "시도교육청": "sido_edu_office",
    "지역교육청": "local_edu_office",
    "지역": "region",
    "정보공시 학교코드": "school_code",
    "학교명": "school_name",
    "설립구분": "foundation_type",
    "1학년(남)": "1st_grade_male",
    "1학년(여)": "1st_grade_female",
    "2학년(남)": "2nd_grade_male",
    "2학년(여)": "2nd_grade_female",
    "3학년(남)": "3rd_grade_male",
    "3학년(여)": "3rd_grade_female",
    "4학년(남)": "4th_grade_male",
    "4학년(여)": "4th_grade_female",
    "5학년(남)": "5th_grade_male",
    "5학년(여)": "5th_grade_female",
    "6학년(남)": "6th_grade_male",
    "6학년(여)": "6th_grade_female",
    "특수학급(남)": "special_class_male",
    "특수학급(여)": "special_class_female",
    "순회학급(남)": "mobile_class_male",
    "순회학급(여)": "mobile_class_female",
    "계(남)": "total_male",
    "계(여)": "total_female",
    "총계": "total",
    "설립유형": "foundation_type",
    "주야구분": "day_night_division",
    "개교기념일": "foundation_anniversary",
    "설립일": "foundation_date",
    "법정동코드": "legal_dong_code",
    "주소내역": "address_detail",
    "상세주소내역": "address_detail2",
    "우편번호": "zip_code",
    "학교도로명 우편번호": "road_address_zip_code"}

# Rename columns based on the columns_mapping dictionary
joined_df = joined_df.rename(columns=columns_mapping)


# ##################################################
# # # plot points and polygon (simple overlay)

# # Pivot the data to create a matrix of the number of boys and girls by grade and school
# pivot_data = joined_df.pivot_table(index='School', columns='Grade', values=['Boys', 'Girls'])
#
# # Create a heatmap using Seaborn
# sns.heatmap(pivot_data)


# ##################################################
# # # basic statistics

# Compute the total number of students by school and gender
# total_students = joined_df.groupby(['school_code']).sum()[['total_male', 'total_female']]
total_students = joined_df.groupby(['school_code']).sum(numeric_only=True)[['total_male', 'total_female']]


# Compute the average number of students by grade and gender
grades = ['1st_grade_male', '2nd_grade_male', '3rd_grade_male', '4th_grade_male', '5th_grade_male', '6th_grade_male']
male_averages = joined_df[grades].mean()
female_averages = joined_df[[col.replace('_male', '_female') for col in grades]].mean()
average_students = pd.concat([male_averages, female_averages], axis=1)
average_students.columns = ['Male', 'Female']

# Compute the percentage of boys and girls in each grade
grades = ['1st_grade', '2nd_grade', '3rd_grade', '4th_grade', '5th_grade', '6th_grade']
boys = joined_df[[grade+'_male' for grade in grades]].sum()
girls = joined_df[[grade+'_female' for grade in grades]].sum()
boy_ratio = boys / (boys + girls)
girl_ratio = girls / (boys + girls)
grade_ratio = pd.concat([boy_ratio, girl_ratio], axis=1)
grade_ratio.columns = ['Male', 'Female']

# Compute the correlation matrix between the number of boys and girls in each grade
grade_counts = joined_df[[grade+'_male' for grade in grades + ['total']]].sum()
correlation_matrix = joined_df[[grade+'_male' for grade in grades]].corrwith(joined_df[[grade+'_female' for grade in grades]])

# Print the results
print('Total number of students by school and gender:\n', total_students)
print('Average number of students by grade and gender:\n', average_students)
print('Percentage of boys and girls in each grade:\n', grade_ratio)
print('Correlation matrix between the number of boys and girls in each grade:\n', correlation_matrix)


total_students = joined_df[['total_male', 'total_female']].sum().sum()
total_boys = joined_df['total_male'].sum()
total_girls = total_students - total_boys
boy_ratio = total_boys / total_students
girl_ratio = total_girls / total_students
print(f"Total number of students: {total_students}")
print(f"Total number of boys: {total_boys}")
print(f"Total number of girls: {total_girls}")
print(f"Boy ratio: {boy_ratio:.2f}")
print(f"Girl ratio: {girl_ratio:.2f}")
'''


# ##################################################
# # # plot points and polygon (simple overlay)
# # fig, ax = plt.subplots(figsize=(10,10))
# #
# # polygons.plot(ax=ax, alpha=0.5, edgecolor='black')
# # joined.plot(ax=ax, color='red', markersize=5)
# #
# # plt.show()
#
# # count the number of points for each polygon
# counts = joined.index.value_counts()
#
# # select polygons with more than one point
# multi_point_polygons = counts[counts > 1].index.tolist()
#
# # print the list of polygons with more than one point
# print(multi_point_polygons)
#
# # generate boys/ratio info of each grade
# grades = ['1학년', '2학년', '3학년', '4학년', '5학년', '6학년']
#
# for grade in grades:
#     total_column = f"{grade}(합계)"
#     columns_to_sum = [f"{grade}(남)", f"{grade}(여)"]
#     joined_df[total_column] = joined_df[columns_to_sum].sum(axis=1)
#
# grades = ['1학년', '2학년', '3학년', '4학년', '5학년', '6학년']
# genders = ['남']
#
# for grade in grades:
#     for gender in genders:
#         column_name = f"{grade}({gender})"
#         column_name_denominator = f"{grade}(합계)"
#         joined_df[column_name + '비율'] = joined_df[column_name]/joined_df[column_name_denominator]
#
# # # plot boys ratio
# # fig, ax = plt.subplots(figsize=(10, 10))
# # joined_df.plot(column='1학년(남)비율', cmap='Blues', ax=ax, legend=True)
# # plt.show()
#
# # for grade in grades:
# #     for gender in genders:
# #         plot_name = f"{grade}(남)비율"
# #         fig, ax = plt.subplots(figsize=(10, 10))
# #         joined_df.plot(column=plot_name, cmap='Blues', ax=ax, legend=True)
# #         plt.savefig(f'{plot_name}.png', dpi=300)
#
# # # create a custom colormap
# # cmap = LinearSegmentedColormap.from_list('custom', [(0, 'red'), (0.5, 'white'), (1, 'blue')])
# #
# # # loop through grades and genders and plot the data
# # for grade in grades:
# #     for gender in genders:
# #         plot_name = f"{grade}({gender})비율"
# #         fig, ax = plt.subplots(figsize=(10, 10))
# #         vmin, vmax = joined_df[plot_name].min(), joined_df[plot_name].max()
# #         norm = plt.Normalize(vmin=vmin, vmax=vmax)
# #         joined_df.plot(column=plot_name, cmap=cmap, ax=ax, norm=norm, legend=True)
# #         plt.savefig(f'{plot_name}.png', dpi=100)
#
#
# # sns.set_theme(style="whitegrid")
# # sns.histplot(data=joined_df, x="1학년(남)비율", kde=True)
# #
# # # create the plot
# # fig, ax = plt.subplots()
# # ax.hist(joined_df["1학년(남)비율"], bins=30, density=True)
# #
# # # set labels and title
# # ax.set_xlabel('Value')
# # ax.set_ylabel('Density')
# # ax.set_title('Normal Distribution')
# #
# # # save the plot to a file
# # plt.savefig('distribution.png', dpi=100)
#
# # Set the font family to one that supports Hangul characters
# plt.rcParams['font.family'] = 'NanumGothic'
#
# sns.set_style("whitegrid")
#
# # create distribution plot
# sns.kdeplot(data=joined_df["1학년(남)비율"], fill=True)
#
# # add histogram line
# sns.histplot(data=joined_df["1학년(남)비율"], color="grey", alpha=.2, kde=True)
#
# # save plot
# plt.savefig("distribution_plot_with_histogram.png", dpi=300)
#
# # # create histogram plot
# # fig, ax = plt.subplots(figsize=(8, 5))
# # sns.histplot(data=joined_df["1학년(남)비율"], ax=ax, color="grey", alpha=.2, kde=True)
# #
# # # add KDE plot on twin Axes
# # ax2 = ax.twinx()
# # sns.kdeplot(data=joined_df["1학년(남)비율"], shade=True, ax=ax2, color='red')
# # ax2.set_ylabel('KDE', color='red')
# # ax2.tick_params(axis='y', labelcolor='red')
# # plt.show()
#
#
# # # Define your data and groups
# # grades = ['1학년', '2학년', '3학년', '4학년', '5학년', '6학년']
# # data = [joined_df[f"{g}(남)비율"] for g in grades]
# #
# # # Create a grid of subplots
# # fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(12, 8))
# # axes = axes.flatten()
# #
# # # Loop over each group of data and plot a histogram on the corresponding subplot
# # for i, (g, d) in enumerate(zip(grades, data)):
# #     ax = axes[i]
# #     sns.histplot(data=d, ax=ax, color="grey", alpha=.2, kde=True)
# #     ax.set_title(g)
# #
# # # Adjust spacing between subplots and add a title to the big plot
# # fig.tight_layout()
# # fig.suptitle('Histograms by Grade')