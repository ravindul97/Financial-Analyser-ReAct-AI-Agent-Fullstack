import pandas as pd

#TO validitity check the dataset
df1 = pd.read_csv("data/processed_csv/dipd_processed_financial_data.csv")
df2 = pd.read_csv("data/processed_csv/rexp_processed_financial_data.csv")

#Printing Dataframes
print(f"df1: {df1}")
print(f"df2: {df2}")

#Info Check
print(f"df1 Info: {df1.info()}")
print(f"df2 Info: {df2.info()}")

# Check for Null Values
print("DF1 Nulls:\n", df1.isnull().sum())
print("DF2 Nulls:\n", df2.isnull().sum())


#Check Duplicates
print("DF1 Duplicates:", df1.duplicated().sum())
print("DF2 Duplicates:", df2.duplicated().sum())

