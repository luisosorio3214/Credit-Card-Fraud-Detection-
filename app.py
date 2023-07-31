# import necessary libraries
import gradio as gr
import shap
import pickle
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import tempfile
import os 
import boto3 
# from pathlib import Path


# load our models 
load_dotenv()
client = boto3.client('s3', aws_access_key_id = os.getenv('aws_access_key'),aws_secret_access_key=os.getenv('aws_secret_key'))
bucket_name = "credit-card-fraud-app"
key = "boost.sav"

with tempfile.TemporaryFile() as fp:
    client.download_fileobj(Fileobj=fp, Bucket=bucket_name, Key=key)
    fp.seek(0)
    boost = pickle.load(fp)

# boost_path = Path(__file__).parents[0] / "Models/boost.sav"
# boost = pickle.load(open(boost_path,"rb"))

# functions

# preprocessing data function
def preprocess(data):
    columns = ['distance_from_home', 'distance_from_last_transaction',
                'ratio_to_median_purchase_price', 'repeat_retailer', 'used_chip',
                'used_pin_number', 'online_order']
    
    df = pd.DataFrame([data], columns = columns)
    
    # convert data type
    df[['repeat_retailer','used_chip','used_pin_number','online_order']] = df[['repeat_retailer','used_chip','used_pin_number','online_order']].astype('int')
    
    return df


# Prediction function with probabilities
def predict(*data):
        df = preprocess(data)
        prob_pred = boost.predict_proba(df)
        return {"Normal": float(prob_pred[0][0]), "Fraud": float(prob_pred[0][1])}

# plot function
def interpret(*data):
        plt.style.use("fivethirtyeight")
        
        df = preprocess(data)
        
        explainer = shap.TreeExplainer(boost)
        shap_values = explainer.shap_values(df)
        scores_desc = list(zip(shap_values[0], df.columns))
        scores_desc = sorted(scores_desc)
        fig_m = plt.figure(tight_layout=True)
        plt.barh([s[1] for s in scores_desc], [s[0] for s in scores_desc])
        plt.title("Feature Shap Values")
        plt.ylabel("Shap Value")
        plt.xlabel("Feature Importance")
        plt.tight_layout()
        
        return fig_m
    
    
    
with gr.Blocks() as demo:
    gr.HTML("""
    <h1 align="center">Credit Card Fraud Prediction System</h1>
    <p>This is a Web App that predicts Whether a Credit Card Transaction is Fraudulent or not. Just input the following parameters and click the predict button. If you want to see the influence that each parameter had on the outcome click the explain button</P>
    """)
    with gr.Row():
        with gr.Column():
            repeated_retailer = gr.Radio(["No","Yes"], type = "index", label = "Repeat Retailer", info ="Was the transaction at a repeated store?")
            
            online_order = gr.Radio(["No","Yes"], type = "index", label = "Online Order", info ="Was the transaction an online order?")
            
            used_chip = gr.Radio(["No","Yes"], type = "index", label = "Used Chip", info ="did the purchase use the security chip of the card?")

            used_pin = gr.Radio(["No","Yes"], type = "index", label = "Used Pin Number", info ="Did the transaction use the pin code of the card?")
            
            distance_home = gr.Number(value = 25, label = "Distance From Home (miles)", info = "How far was the transaction from the card owner's house? (in Miles)")
            
            distance_last = gr.Number(value = 5, label = "Distance From Last Transaction (miles)", info = "How far away was the it from the last transaction that happened? (in Miles)")
            
            gr.HTML("""
                <h4 align="center">Ratio Median Purchase Price Equation</h4>
                    """)
            ratio_median = gr.Number(value = 1.8, label = "Ratio Median Purchase Price", info = "Divide the purchase price by card owners median purchase price?")
        
            
        with gr.Column():
            label = gr.Label()
            plot = gr.Plot()
            with gr.Row():
                predict_btn = gr.Button(value="Predict")
                interpret_btn = gr.Button(value="Explain")
            predict_btn.click(
                predict,
                inputs= [
                    distance_home,
                    distance_last,
                    ratio_median,
                    repeated_retailer,
                    used_chip,
                    used_pin,
                    online_order   
                ],
                outputs=[label],
            )
            interpret_btn.click(
                interpret,
                inputs=[
                    distance_home,
                    distance_last,
                    ratio_median,
                    repeated_retailer,
                    used_chip,
                    used_pin,
                    online_order   
                ],
                outputs=[plot],
            )

demo.launch()