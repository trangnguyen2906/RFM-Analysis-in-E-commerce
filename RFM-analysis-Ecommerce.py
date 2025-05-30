# Import Packages
"""

!pip install ydata-profiling
!pip install squarify

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from ydata_profiling import ProfileReport
import squarify #for treemap

"""# 1. Understand Data

## 1.1. Load Dataset
"""

ecommerce = pd.read_csv('/content/drive/MyDrive/UNIGAP/Python/Final Project/ecommerce retail.xlsx - ecommerce retail.csv')
segmentation = pd.read_csv('/content/drive/MyDrive/UNIGAP/Python/Final Project/segmentation.csv')
df = ecommerce.copy()
df1 = segmentation.copy()

"""## 1.2. Check values and datatypes"""

# Check datatypes
print(df.info())
# Check numerical data
print(df.describe())
df.head()

"""## 1.3. Deep dive into and deal with inproper datatypes and data values
- The datatypes of InvoiceNo, StockCode, Description, InvoiceDate, UnitPrice, CustomerID, Country is FALSE
- Why quantity has negative values?

### ***Datatypes***
"""

#StockCode, Description, Country, InvoiceNo -- Datatype: String
df = df.astype({'StockCode':'string', 'Description':'string', 'Country':'string', 'InvoiceNo': 'string'})

#InvoiceDate -- datetime
df['InvoiceDate'] = df['InvoiceDate'].astype('datetime64[ns]')

#UnitPrice -- float
df['UnitPrice'] = df['UnitPrice'].str.replace(',','.').astype('float')

#CustomerID -- int64
df['CustomerID'] = df['CustomerID'].astype('Int64')

ProfileReport(df)

print(df.info())

"""### ***Data values***
- Check the negative value and possible reasons
  + Quantity col has negative values
      - Đa số negative values ở cột Quantity là do đơn hàng bị cancel -> Drop các rows đó đi
  + UnitPrice has negative values -> drop  

"""

df.describe()

# Check negative values in Quantity column
df[df['Quantity'] < 0]
  ## Almost negative value in Quantity col has InvoiceNo start with 'C' -> Check
check_cancel = df['InvoiceNo'].str.startswith('C')
negative_quan_cancel = df[(df['Quantity'] < 0) & (check_cancel == True)]
  ### other negative quantity
negative_quan_nocancel = df[(df['Quantity'] < 0) & (check_cancel == False)]

#Check negative values in UnitPrice col
df[df['UnitPrice'] < 0]

#Drop rows that cancel and has negative values in Quantity column
df = df[~((df['Quantity'] < 0) & (check_cancel == True))]
#Drop negative values in UnitPrice col
df = df[df['UnitPrice'] > 0]

df.describe()

"""# 2. Missing and Duplicate Data

## 2.1. Detect missing data
"""

check_null = pd.DataFrame(df.isnull().sum())
check_null['%missing'] = check_null[0] / len(df) * 100
check_null.columns = ['count', '%missing']
check_null # Missing many values in CustomerID column (~25%)

"""**Check possible reasons for missing values in customerID column**"""

check_missing = df.copy()
check_missing

## Check if missing CustomerIDs are related to cancelled transactions
cancelled = df[df['CustomerID'].isnull() & df['InvoiceNo'].str.startswith('C')]
print(cancelled)

## Check if missing CustomerIDs are linked to specific countries
missing_countries = df[df['CustomerID'].isnull()]['Country'].value_counts()
print("\nCountries with missing CustomerID:\n", missing_countries)

check_missing['MonthYear'] = df['InvoiceDate'].dt.to_period('M')
# Count missing CustomerID per month
missing_by_month = check_missing[check_missing['CustomerID'].isnull()]['MonthYear'].value_counts().sort_index()
print(missing_by_month)

"""**Nhận xét**
1. Missing values chỉ nằm ở col CustomersID
2. CustomerID bị thiếu k lquan đến đơn hàng bị huỷ
3. Phần lớn missing values nằm ở thị trường UK

## 2.2. Check duplicated data
"""

df[df.duplicated()]

"""## 2.3. Dealing with missing and duplicate data
- Missing values: Only customerID is missing -> Doing RFM model need to group based on CustomerID --> Drop 25% missing value in CustomerID col
- Duplicate data: drop duplicated rows
"""

# Missing values
df = df.dropna(subset=['CustomerID'])
# Duplicated rows
df_clean = df.drop_duplicates().copy()
df_clean.isnull().sum()

"""# 3. Data Processing

## 3.1. Calculate RFM
"""

df_clean

df_clean['Date'] = df_clean['InvoiceDate'].dt.normalize()
df_clean['MonthYear'] = df_clean['InvoiceDate'].dt.to_period('M')
df_clean['Cost'] = df_clean['Quantity']*df_clean['UnitPrice']
df_clean

# Define last day in dataset
last_day = df_clean['Date'].max()

# Create RFM dataframe
RFM_df = df_clean.groupby('CustomerID').agg(
    Recency=('Date', lambda x: last_day - x.max()),
    Frequency=('InvoiceNo', 'nunique'),
    Monetary=('Cost', 'sum'),
    Start_day=('Date', 'min')
).reset_index()

RFM_df['Recency'] = RFM_df['Recency'].dt.days.astype('int16')
RFM_df['Recency_reverse'] = -RFM_df['Recency']
RFM_df['Start_Month'] = RFM_df['Start_day'].apply(lambda x: x.replace(day=1))
RFM_df.head()

"""## 3.2. RFM_score

- Meaning of customers segment based on RFM_score
1. Champions: bought recently, buy often and spend the most
2. Loyal:
3. Potential Loyalist:
4. New Customers
5. Promising:
6. Need Attention:
7. About to Sleep
8. At Risk: Customers who have spent a lot but whose buying frequency has decreased significantly.
9. Cannot Lose Them: Customers who used to shop frequently and spend a lot but haven’t purchased recently.
10. Hibernating customers: Long-time customers who haven’t made purchases in a while.
11. Lost customers
"""

RFM_df.info()

#Calculate RFM score
RFM_df['R_score'] = pd.qcut(RFM_df['Recency'], 5, labels=[5, 4, 3, 2, 1]).astype(str)
RFM_df['F_score'] = pd.qcut(RFM_df['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(str)
RFM_df['M_score'] = pd.qcut(RFM_df['Monetary'], 5, labels=[1, 2, 3, 4, 5]).astype(str)
RFM_df['RFM_score'] = RFM_df['R_score'] + RFM_df['F_score'] + RFM_df['M_score']
RFM_df

#Segment Customers
segment = pd.read_csv('/content/drive/MyDrive/UNIGAP/Python/Final Project/segmentation.csv')
segment['RFM Score'] = segment['RFM Score'].str.split(',')
# Tách array của RFM score
segment = segment.explode('RFM Score').reset_index().drop(columns=['index'])
segment

#Mapping with RFM_df
RFM_df['RFM_score'] = RFM_df['RFM_score'].astype(str).str.strip()
segment['RFM Score'] = segment['RFM Score'].astype(str).str.strip()
RFM_df_merge = RFM_df.merge(segment, left_on='RFM_score', right_on='RFM Score', how='left')
RFM_df_merge

"""# 4. Visualizations

## 4.1. Distribution of R,F,M
- Nhận xét:
  + Từ Distribution của Recency: Majority of customers are recent purchasers -- also long tail of customers not purchased for long time (in-active customers)
  + Từ distribution của Frequency: Majority purchased only 1-2 times, very few customers buy repeatedly -- low customers retention rate (Key weakness)
  + Từ distribution của Monetary: Most customers spend small amounts.
"""

fig, ax = plt.subplots(figsize=(10, 6))
color=sns.color_palette('Blues')[3]
sns.histplot(RFM_df_merge['Recency'], ax=ax, kde=True, stat='density', color = color , edgecolor='black')  # add binwidth
ax.set(xlabel='Recency', ylabel='Distribution', title='Distribution of Recency')
plt.show()

fig, ax = plt.subplots(figsize=(10, 6))
color=sns.color_palette('Blues')[3]
sns.histplot(RFM_df_merge['Frequency'], ax=ax, kde=True, stat='density',
             binwidth=1, color = color , edgecolor='black')  # add binwidth
ax.set(xlabel='Frequency', ylabel='Distribution', xlim=(0, 20), title='Distribution of Frequency')
plt.show()

fig, ax = plt.subplots(figsize=(10, 6))
color=sns.color_palette('Blues')[3]
sns.histplot(RFM_df_merge['Monetary'], ax=ax, kde=True, stat='density',color = color , edgecolor='black', binwidth = 500)  # add binwidth
ax.set(xlabel='Monetary', ylabel='Distribution', xlim = (-1000,15000), title='Distribution of Monetary')
plt.show()

"""## 4.2. Treemap based on 11 Customers segments"""

segment_counts = RFM_df_merge['Segment'].value_counts()
total = segment_counts.sum()
labels = [f"{seg}\n({count*100/total:.1f}%)"
          for seg, count in zip(segment_counts.index, segment_counts.values)]

# Create subplots
fig, axes = plt.subplots(1, 2, figsize=(20, 8))  # 1 row, 2 columns

# Left: Treemap
squarify.plot(sizes=segment_counts.values,
              label=labels,
              color=sns.color_palette('Paired'),
              pad=True,
              alpha=0.8,
              ax=axes[0])
axes[0].set_title('Treemap of Customer Segments')
axes[0].axis('off')

#Right: Bar Chart
bar = sns.countplot(data=RFM_df_merge,
                    x='Segment',
                    order=segment_counts.index,
                    palette='Paired',
                    ax=axes[1])
axes[1].set_title('Number of Customers in Each Segment')
axes[1].set_xlabel('Customer Segment')
axes[1].set_ylabel('Number of Customers')
axes[1].tick_params(axis='x', rotation=45)

# Add data labels
for p in bar.patches:
    height = p.get_height()
    axes[1].text(p.get_x() + p.get_width() / 2,
                 height + 10,
                 f'{height:.0f}',
                 ha='center',
                 fontsize=9)

plt.tight_layout()
plt.show()

Monetary_total = RFM_df_merge.groupby('Segment')['Monetary'].sum()

# Tính tổng Monetary toàn bộ
total = RFM_df_merge['Monetary'].sum()

# Tạo labels với % đóng góp
labels = [f"{seg}\n ({count*100/total:.1f}%)"
          for seg, count in zip(Monetary_total.index, Monetary_total.values)]

# Treemap
plt.figure(figsize=(14, 8))
squarify.plot(
    sizes=Monetary_total.values,
    label=labels,
    color=sns.color_palette('Paired'),
    pad=True,
    alpha=0.9
)
plt.title('Treemap of Customer Segments by Total Revenue', fontsize=14)
plt.axis('off')
plt.show()

"""## 4.3. Recommendation for Marketing Campaign
**Divide 11 customers segments into 3 smaller groups based on their behavior**
1. Loyal & VIP Customers: Champions, Loyal (R&F_score = 4/5; Contribute apprxml 75% of total revenue)
2. Potential Customers: Potential Loyalist, Promising, Need Attention, New Customers (R&F score moderate->high 2,3,4,5 -- lower share of revenue but strong potential)
3. At Risk & Lost Customers: At Risk, Cannot Lose Them, Hibernating Customers, Lost Customers, About To Sleep (low recency score -> haven't purchased for long time)
"""

def regroup_segment(segment):
    if segment in ['Champions', 'Loyal']:
        return 'Loyal & VIP Customers'
    elif segment in ['Potential Loyalist', 'New Customers', 'Promising', 'Need Attention']:
        return 'Potential Customers'
    else:
        return 'At Risk & Lost Customers'

RFM_df_merge['Customer_Group'] = RFM_df_merge['Segment'].apply(regroup_segment)
RFM_df_merge

plt.figure(figsize=(8, 5))
sns.countplot(data=RFM_df_merge, x='Customer_Group', palette='Set2')
plt.title('Customer Distribution by New Groups')
plt.xticks(rotation=15)
plt.show()

"""**Nhận xét**
1. Gratitude Campaign mainly on the Loyal & VIP Customers group: bcz they have highest RFM scores, contributes around 75% revenue, purchase behavior is stable and frequent, they are most likely to respond positively to gratitude campaigns and loyalty incentives
- How?: Appreciate, offer exclusive rewards, personalize experience (by tracking top products they often buy to provide exclusive product package vouchers), strengthen loyalty
2. 2nd group can be included in the campaign: A gratitude campaign can help nurture and encourage them to buy more regularly
"Thank you and keep shopping" approach, convert them into loyal customers
3. Not recommend to run MKT campaign for 3rd group: not cost-effective and low conversion rates

## 4.4. Dig deeper into each group of customers

### 4.4.1. Correlation btw R,F,M of each groups
- Loyal & VIP Customers: Frequency vs Monetary: Strong positive correlation (0.55)
- No strong relation in R,F,M score of 2nd and 3rd group
"""

# Loyal and VIP Customers group
cols = ['Recency','Monetary', 'Frequency']
sns.heatmap(RFM_df_merge[cols][RFM_df_merge['Customer_Group'].isin(['Loyal & VIP Customers'])].corr(), annot=True, cmap='Blues')

#Potential Customers group
cols = ['Recency','Monetary', 'Frequency']
sns.heatmap(RFM_df_merge[cols][RFM_df_merge['Customer_Group'].isin(['Potential Customers'])].corr(), annot=True, cmap='Blues')

#At Risk & Lost Customers
cols = ['Recency','Monetary', 'Frequency']
sns.heatmap(RFM_df_merge[cols][RFM_df_merge['Customer_Group'].isin(['At Risk & Lost Customers'])].corr(), annot=True, cmap='Blues')

"""### 4.4.2. Scatterplot Frequency vs Monetary (only for Loyal & VIP Customers)"""

# Filter data
vip_df = RFM_df_merge[RFM_df_merge['Customer_Group'] == 'Loyal & VIP Customers']
filtered_df = vip_df[(vip_df['Frequency'] < 100) & (vip_df['Monetary'] < 200000)]

# Create subplots
fig, axes = plt.subplots(1, 2, figsize=(18, 6))

# Left plot - With outliers
sns.regplot(
    data=vip_df,
    x='Frequency',
    y='Monetary',
    scatter_kws={'alpha': 0.7, 's': 40},
    ax=axes[0]
)
axes[0].set_title('Frequency vs Monetary (With Outliers)')
axes[0].set_xlabel('Frequency')
axes[0].set_ylabel('Monetary')
axes[0].grid(True)

# Right plot - Without outliers
sns.regplot(
    data=filtered_df,
    x='Frequency',
    y='Monetary',
    scatter_kws={'alpha': 0.7, 's': 40},
    ax=axes[1]
)
axes[1].set_title('Frequency vs Monetary (Without Outliers)')
axes[1].set_xlabel('Frequency')
axes[1].set_ylabel('Monetary')
axes[1].grid(True)

plt.tight_layout()
plt.show()

"""## 4.5. Potential customers -> Loyal customers
- Trong 4 customer segments thuộc potential customers group, nhóm nào nên tập trung vào yếu tố gì, cách tiếp cận ntn để chuyển thành loyal customers???
"""

#mean, median of segments except at risk and lost customers
comparison_df = RFM_df_merge[RFM_df_merge['Customer_Group'] != 'At Risk & Lost Customers']
comparison_summary = comparison_df.groupby('Segment')[['Recency', 'Frequency', 'Monetary']].agg(['mean', 'median']).reset_index()
comparison_summary.columns = ['_'.join(col).strip('_') for col in comparison_summary.columns.values]
comparison_summary['AOV_mean'] = comparison_summary['Monetary_mean'] / comparison_summary['Frequency_mean']
comparison_summary['AOV_median'] = comparison_summary['Monetary_median'] / comparison_summary['Frequency_median']
comparison_summary

fig, axes = plt.subplots(2, 2, figsize=(16, 10))
sns.barplot(x='Recency_median', y='Segment', data=comparison_summary, ax=axes[0, 0], color='navy').set(title='Recency (Median)')
sns.barplot(x='Frequency_median', y='Segment', data=comparison_summary, ax=axes[0, 1], color='green').set(title='Frequency (Median)')
sns.barplot(x='Monetary_median', y='Segment', data=comparison_summary, ax=axes[1, 0], color='orange').set(title='Monetary (Median)')
sns.barplot(x='AOV_median', y='Segment', data=comparison_summary, ax=axes[1, 1], color='darkred').set(title='AOV (Median)')
plt.tight_layout()
plt.show()

"""**Recommendations**

"""
