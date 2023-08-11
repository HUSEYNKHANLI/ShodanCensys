import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import StandardScaler

# Load the data
data = pd.read_csv('shodan_results.csv')

# Handle missing values (for simplicity, we'll replace NaN with empty strings for the 'data' column)
data['data'].fillna("", inplace=True)

# Tokenize the 'data' field using CountVectorizer
vectorizer = CountVectorizer(max_features=1000, stop_words='english')
X = vectorizer.fit_transform(data['data'])
tokenized_data = pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names_out())

# If you have numerical data that you'd like to normalize/standardize, you can do so here.
# For instance, if you had a column 'column_name_to_standardize', you'd do:
# scaler = StandardScaler()
# data['column_name_to_standardize'] = scaler.fit_transform(data[['column_name_to_standardize']])

# Save the tokenized data for future use (you can save it in the same DataFrame or a new one)
data = pd.concat([data, tokenized_data], axis=1)
data.drop(columns='data', inplace=True)  # Drop the original 'data' column
data.to_csv('preprocessed_shodan_results.csv', index=False)
