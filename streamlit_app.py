# expects "data consistent" CSV files exported from Assets in JIRA
# The program then creates a nice table to applicable controls

import streamlit as st
import pandas as pd
import base64

import plotly.graph_objects as go

#import numpy as np
#import plotly.express as px
#import plotly.figure_factory as ff
#import plotly.graph_objects as go

def create_download_link(val, filename):
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'


def read_data_files(processes,assets,threats,controls):
    try:
        df_processes = pd.read_csv(processes).drop(['Created', 'Updated'], axis=1)
        df_assets = pd.read_csv(assets).drop(['Created', 'Updated'], axis=1)
        df_threats = pd.read_csv(threats).drop(['Created', 'Updated'], axis=1)
        df_controls = pd.read_csv(controls).drop(['Created', 'Updated'], axis=1)
    except:
        st.write("Agh missing data file!")
        quit(600)
    return df_processes, df_assets, df_threats, df_controls

def get_matching_controls(df_controls, df_matching_threats):
    data_controls = pd.concat([df_matching_threats["Control_1"], df_matching_threats["Control_2"],
                               df_matching_threats["Control_3"], df_matching_threats["Control_4"],
                               df_matching_threats["Control_5"],
                               df_matching_threats["Control_6"], df_matching_threats["Control_7"]])
    data_controls_list = data_controls.dropna().tolist()

    # remove any duplicates
    data_controls_list = list(set(data_controls_list))

    # create the dataframe
    matching_controls = df_controls[df_controls["Key"].isin(data_controls_list)]
    matching_controls.sort_values(by='Name', inplace=True)

    new_df = matching_controls[['Name', 'Description', "Confluence page","Key"]].set_index('Name')
    return new_df

def print_control_count(df_controls, df_matching_threats,charts):
    data_controls = pd.concat([df_matching_threats["Control_1"], df_matching_threats["Control_2"],
                               df_matching_threats["Control_3"], df_matching_threats["Control_4"],
                               df_matching_threats["Control_5"],
                               df_matching_threats["Control_6"], df_matching_threats["Control_7"]])
    data_controls_list = data_controls.dropna().tolist()
    # convert to pandas DataFrame
    df_data_controls_list = pd.DataFrame(data_controls_list, columns=['Key'])
    # count the occurrence of each unique control
    df_control_count = df_data_controls_list['Key'].value_counts().reset_index()
    # rename columns
    df_control_count.columns = ['Key', 'Count']


    #st.write(df_controls)
    #add description
    # merge the two dataframes based on the common column "control"
    df_control_count = pd.merge(df_control_count, df_controls, left_on='Key', right_on='Key')
    #df_control_count =df_control_count.drop(columns=["Key"])

    #st.write(data_controls_list)
    st.write("Significance of control")
    st.write(df_control_count)

    if charts:
        df_control_count = df_control_count.drop(["Description","Confluence page"], axis=1)
        fig = go.Figure(data=[go.Table(
            header=dict(values=list(df_control_count.columns),
                        fill_color='paleturquoise',
                        align='left'),
            columnwidth=[1, 1,6,2],
            cells=dict(values=[df_control_count[col] for col in df_control_count.columns],
                       fill_color='lavender',
                       align='left')) ])

        fig.update_layout(height=len(df_control_count)*40,width=1000)
        st.plotly_chart(fig)

    return

def print_threats_as_chart(df_threats):
    df_threats = df_threats.reset_index().rename(columns={'index': 'Threat'})
    fig = go.Figure(data=[go.Table(
        header=dict(values=list(df_threats.columns),
                    fill_color='paleturquoise',
                    align='left'),
        columnwidth=[2,1,1,1,6],
        cells=dict(values=[df_threats[col] for col in df_threats.columns],
                   fill_color='lavender',
                   align='left')) ])

    fig.update_layout(height=len(df_threats)*90,width=1000)
    st.plotly_chart(fig)
    return

def print_controls(df_matching_controls):
    for index, row in df_matching_controls.iterrows():
        try:
            name = row['Name']
        except:
            name = index
        description = row['Description']
        confluence_page = row['Confluence page']
        st.markdown("**" + name + "**")
        if not pd.isna(description):
            st.markdown("_" + description + "_")
        if not pd.isna(confluence_page):
            st.write(confluence_page)
    return

def print_the_threats_and_controls(df_controls,df_filtered_threats,charts):

    df_controls_for_filtered_threats = get_matching_controls(df_controls, df_filtered_threats)

    #print popularity/importance of controls
    print_control_count(df_controls, df_filtered_threats, charts)
    #st.write(df_controls_for_filtered_threats)

    for index, row in df_filtered_threats.iterrows():
        name = index
        score = str(row['Score'])
        st.markdown("### " + name + " (score="+score+")")
        df_controls_for_this_row = get_matching_controls(df_controls,pd.DataFrame([row]))
        print_controls(df_controls_for_this_row)
    return

#show details by selected business process
def business_process(processes,assets,threats,controls,charts):
    df_processes, df_assets, df_threats, df_controls = read_data_files(processes, assets, threats, controls)

    # create a list of the business processes
    if processes:
        process_list = df_processes["Name"].tolist()
        this_process = st.selectbox("Select the process to dive into", process_list)

    go = st.button("Continue...")

    if go:
        #######################
        #  processes
        #######################
        if this_process:
            filtered_df = df_processes.loc[df_processes["Name"] == this_process]
            data_assets = pd.concat(
                [filtered_df["Data Asset_1"], filtered_df["Data Asset_2"], filtered_df["Data Asset_3"],
                 filtered_df["Data Asset_4"]])
            data_asset_list = data_assets.dropna().tolist()
            # st.write(data_asset_list)
        else:
            st.write("No process selected.")

        #########################
        # data assets
        #########################
        # now filter the data assets to only those in the list
        # Create a new dataframe of only the matching rows
        matching_assets = df_assets[df_assets["Key"].isin(data_asset_list)]
        matching_assets.sort_values(by='Name', inplace=True)

        st.subheader("Data Assets")
        new_df = matching_assets[['Name', 'Description']].set_index('Name')
        st.table(new_df)

        #########################
        # threats
        #########################
        # now get the threats
        data_threats = pd.concat([matching_assets["Vulnerability_Threat"], matching_assets["Vulnerability_Threat_2"],
                                  matching_assets["Vulnerability_Threat_3"],
                                  matching_assets["Vulnerability_Threat_4"]])
        data_threat_list = data_threats.dropna().tolist()

        # threat_mentions =

        # remove any duplicates
        data_threat_list = list(set(data_threat_list))

        st.subheader("Threats")
        # st.write(data_threat_list)
        matching_threats = df_threats[df_threats["Key"].isin(data_threat_list)]
        matching_threats.sort_values(by='Name', inplace=True)

        new_df = matching_threats[['Name', 'Likelihood', "Impact", "Score", "Rationale"]].set_index('Name').sort_values(by='Score', ascending=False)
        st.table(new_df)

        #if charts:
        #    print_threats_as_chart(new_df)



        df_filtered_threats = matching_threats[
            ['Name', 'Likelihood', "Impact", "Score", "Rationale", "Key", "Control_1", "Control_2", "Control_3",
             "Control_4", "Control_5", "Control_6", "Control_7"]].set_index('Name')

        print_the_threats_and_controls(df_controls, df_filtered_threats,charts)


    #  export_as_pdf = True #st.button("Export Report")

    #  if export_as_pdf:
    #      pdf = FPDF()
    #      pdf.add_page()
    #      pdf.set_font('Arial', 'B', 16)
    #      pdf.cell(40, 10, report_text)

    #      html = create_download_link(pdf.output(dest="S").encode("latin-1"), "test")
    #      st.markdown(html, unsafe_allow_html=True)
    return

# provide overview of all controls and threats
def overview(processes,assets,threats,controls,charts):
    df_processes, df_assets, df_threats, df_controls = read_data_files(processes, assets, threats, controls)

    # print things that don't look right or need improvement
    st.subheader("Warnings")

    df_threats_with_no_controls = df_threats[df_threats['Control_1'].isnull()]
    df_threats_with_no_controls = df_threats_with_no_controls[['Name', 'Likelihood', "Impact", "Score", "Rationale","Key"]].set_index('Name').sort_values(by='Score', ascending=False)

    st.write("Threats with no controls ("+str(df_threats_with_no_controls.shape[0])+" missing)")
    st.write(df_threats_with_no_controls)

    #--------------------------
    # Controls not applied
    #----------------------
    controls_applied = pd.concat([df_threats["Control_1"], df_threats["Control_2"],
                               df_threats["Control_3"], df_threats["Control_4"],
                               df_threats["Control_5"],
                               df_threats["Control_6"], df_threats["Control_7"]]).dropna().to_frame()
    controls_applied = controls_applied.rename(columns={'index': 'Key', 0: 'Key'})


    # merge the two dataframes based on the 'Key' column, identifying which rows are not matching
    df_merged = df_controls.merge(controls_applied, on='Key', how='left', indicator=True)

    # filter out rows that match
    df_unmatched_controls = df_merged[df_merged['_merge'] == 'left_only'].drop(columns=['_merge'])
    st.write("Controls not applied ("+str(df_unmatched_controls.shape[0])+" unused)")
    st.write(df_unmatched_controls)

    # print hightlights
    st.subheader("Threats")
    threat_cutoff = st.selectbox("Show threats above...",["10","9","8","7","6","5","4"])
    cutoff = int(threat_cutoff)

    df_filtered_threats = df_threats[df_threats['Score'] >= cutoff]
    df_filtered_threats = df_filtered_threats[['Name', 'Likelihood', "Impact", "Score", "Rationale", "Key","Control_1","Control_2","Control_3","Control_4","Control_5","Control_6","Control_7"]].set_index(
        'Name').sort_values(by='Score', ascending=False)

    st.write(df_filtered_threats)
    print_the_threats_and_controls(df_controls,df_filtered_threats, charts)


    #st.write("Highest scoring threats (those equal to and above "+threat_cutoff+")")
    #st.write("Data assets and business processes impacted by threat")
    #st.write("Controls impacting the highest scoring threats")

    return

#setup the system
st.write("Upload all the files")
#processes = st.sidebar.file_uploader("select processes csv")
#assets = st.sidebar.file_uploader("select data assets csv")
#threats = st.sidebar.file_uploader("select vulnerabilities/threats csv")
#controls = st.sidebar.file_uploader("select controls csv")

processes = st.file_uploader("select processes csv")
assets = st.file_uploader("select data assets csv")
threats = st.file_uploader("select vulnerabilities/threats csv")
controls = st.file_uploader("select controls csv")

#PDF output
report_text = ""

# -------------------
#
#  Several options:
#  1. info for each business area
#  2. company overview: unused controls, most used controls, highest threats
#
# -------------------

main_option = st.radio("Select analysis required", ["Business Area","Overview"])
charts = st.radio("Show tables as graphic", ["yes","no"])=="yes"

if main_option == "Business Area":
    business_process(processes,assets,threats,controls,charts)
if main_option == "Overview":
    overview(processes,assets,threats,controls,charts)

