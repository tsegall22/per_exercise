## imports
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import datetime

## observe the data
filepath = r"C:\Projects\Deep Learning Academy\PerimeterX\Analysts_test1.csv"
data = pd.read_csv(filepath)
print(data.head(5))
print(data.shape)

# The data is with a shape of (301983,4)
# remove columns that have only one unique value - these columns are not meaningful
unique_cols = data.apply(pd.Series.nunique)
cols_to_remove = [col for ind, col in enumerate(unique_cols.index) if unique_cols[ind] == 1]
data.drop(cols_to_remove, axis=1, inplace=True)
print(data.columns)

# The column "path" was removed - had only one unique value "login". All rows are login attempts
## The f0_ column looks like epoch timestamps. We will convert to date times and sort values
data['f0_'] = data["f0_"].apply(lambda x: datetime.datetime.fromtimestamp(x // 1000000))
data = data.sort_values(by="f0_")

# we will draw a histogram of the number of login every minute in the data
num_minutes = int(np.round((data["f0_"].iloc[-1] - data["f0_"].iloc[0]).total_seconds()/60))
plt.figure()
plt.hist(data["f0_"], num_minutes)
plt.xlabel("date time")
plt.ylabel("counts")
plt.title("Number of login attempts per minute")

# it clearly looks from the histogram that there are times at which there are much more login attempts
## we will find a threshold on the number of login attempts per minute
bin_range = pd.date_range(data["f0_"].iloc[0], data["f0_"].iloc[-1], freq="1min")
f0_hist, _  = pd.cut(data["f0_"], bins=bin_range, include_lowest=True, right=False, retbins=True)
f0_hist = f0_hist.value_counts()
f0_pctile_per_minute = f0_hist.describe(percentiles=np.arange(0.01, 1, 0.001)).iloc[4:]
print(f0_pctile_per_minute)

# we can see that 99.3 percent of the minute bins have less than 894 logins per minute.
# We will pick a a threshold of 894 logins per minute meaning that there is an anomaly if there are
# more than 894 logins per minute. We will mention the periods that these anomalies appeared
# by aggregating close time stamps
login_per_minute_threshold = 894
anomalies1 = f0_hist[f0_hist > login_per_minute_threshold]
anomalies1 = anomalies1.reset_index()
times = pd.Series([anomalies1["index"][i].mid for i in range(len(anomalies1))]).sort_values()
new_period_inds = np.sort(np.append(np.where(times.diff() > pd.Timedelta(minutes=2))[0], np.array([0,len(times)])))
print("The following periods have unusual number of logins")
for period_ind in range(len(new_period_inds)-1):
    print(str(times.iloc[new_period_inds[period_ind]]) + "  -  " + str(times.iloc[new_period_inds[period_ind+1]-1]))


## We will try to find another anomaly - number of login attempts from the same ip in an interval of one minute
# lets check the histogram of the ips
unique_ips = data["socket_ip"].unique()
print("the number of unique ips is : " + str(unique_ips.shape[0]))
ip_hist = data["socket_ip"].value_counts(sort=False)
plt.figure(figsize=(16, 6))
ip_hist.plot()
plt.xlabel("ip_number")
plt.ylabel("counts")

# There are clearly some ips that try to login more than others
# We will calculate the maximum number of login attempts in one minute for each ip
ips_max_login = pd.DataFrame(index = unique_ips, columns=["max_login_per_minute"])
for ip in unique_ips:
    ip_data = data[data["socket_ip"] == ip]
    bin_range = pd.date_range(ip_data["f0_"].iloc[0], ip_data["f0_"].iloc[-1] + pd.Timedelta(minutes=1), freq="1min")
    f0_hist, _ = pd.cut(ip_data["f0_"], bins=bin_range, include_lowest=True, right=False, retbins=True)
    ips_max_login.loc[ip] = f0_hist.value_counts().max()

## Lets look at the percentiles of maximum logins in one minute for each ip
ips_max_login = ips_max_login.sort_values("max_login_per_minute")
print(ips_max_login)
max_ip_login_percentiles = ips_max_login.describe(percentiles=np.arange(0.01, 1, 0.0001)).iloc[4:-1]
print(max_ip_login_percentiles)

## we can see that 99.9699% of the ips have a maximum number of login attempts per one minute
#  less than 20. This could be a good threshold to detect an anomaly of an ip that is trying
#  to login too many times in one minute
max_logins_by_ip_threshold = 20
print("The following ips have significant maximum greater amount of login attempts per minute than others: ")
print(list(ips_max_login[ips_max_login["max_login_per_minute"]>max_logins_by_ip_threshold].index))




# a = max_ip_login_percentiles.copy()
# print(a)
# a.index = a.index.str.replace("%", "").astype(float)
# f0_pctile_per_minute = f0_hist.describe(percentiles=np.arange(0.01, 1, 0.001)).iloc[4:]
# a = data.groupby(["socket_ip"])
#
#
# a = data["socket_ip"].value_counts().describe(percentiles=np.arange(0.01, 1, 0.001)).iloc[4:-1]
#
# a = a.reset_index()
# a = a.rename(columns={"index":"percentile"})
# ax = a.plot(xticks=a.index[::100])
# ax.set_xticklabels(a["percentile"]/100)
# a.plot()
# a[-50:]
# a
# out.value_counts(sort=False).to_frame().plot()
# plt.hist(out.value_counts(sort=False), len(bin_range))
#
# a = out.value_counts(sort=True)
#
# ## we will check the ip appearance and decide on a threshold
# ip_hist = data["socket_ip"].value_counts()
# data["socket_ip"].value_counts().describe(percentiles=np.arange(0.01, 1, 0.0001)).iloc[4:].plot()
# # data["socket_ip"].value_counts().describe(percentiles=np.arange(0.01, 1, 0.001)).iloc[4:].plot()
# data.groupby('socket_ip').size().sort_values()
#
# data["f0_"].value_counts().describe(percentiles=np.arange(0.01, 1, 0.001)).iloc[4:].plot()
# a = data.groupby(["f0_", "socket_ip"], as_index=False ).count()
# b = data.groupby(["socket_ip"]).mean().sort_values(by="f0_")
# c = data.sort_values(by="f0_")
# # it is not chrnological, we will assume that this column is not a time stamp
# # Second column appears to be some technical details about the customer software environment
# # Third column appears to be the ip
# # Fourth column appears to be the path
#
# # drawing a histogram of f0_
# # plt.hist(data["f0_"], bins=len(data["f0_"].unique()))
# plt.hist(data["f0_"])
# sns.distplot(data["f0_"])
# plt.hist(data["socket_ip"])
# data["socket_ip"].value_counts().hist()
#
#
# ip_hist = data["socket_ip"].value_counts().sort_values(ascending=False)
# ip_hist.head(100)
# print(ip_hist.shape)
