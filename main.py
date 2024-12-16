import kagglehub
import pandas as pd
import os
import numpy as np
import plotly.graph_objects as go

print("Processing NASA battery dataset...\nPlease wait...")

file_path = kagglehub.dataset_download("patrickfleith/nasa-battery-dataset")
base_path = f"{file_path}\\cleaned_dataset"
data_path = os.path.join(base_path, "data")
metadata_file = os.path.join(base_path, "metadata.csv")

metadata = pd.read_csv(metadata_file)

battery_ids = []
relative_ages = []
charge_discharge_cycles = []
battery_impedance = []
electrolyte_resistance = []
charge_transfer_resistance = []

for battery_id in metadata["battery_id"].unique():
    battery_metadata = metadata[metadata["battery_id"] == battery_id]
    
    for relative_age, (_, row) in enumerate(battery_metadata.iterrows()):
        filename = row['filename']
        file_path = os.path.join(data_path, filename)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        test_data = pd.read_csv(file_path)
        
        if 'Battery_impedance' in test_data.columns:
            real_imag_parts = test_data['Battery_impedance'].str.extract(r"\((.+)\+(.+)j\)")
            real_part = pd.to_numeric(real_imag_parts[0], errors='coerce')
            imag_part = pd.to_numeric(real_imag_parts[1], errors='coerce')
            magnitude = np.sqrt(real_part**2 + imag_part**2)
            avg_impedance = magnitude.mean()
        else:
            avg_impedance = None
        
        battery_ids.append(row['battery_id'])
        relative_ages.append(relative_age)
        charge_discharge_cycles.append(row['test_id'])
        battery_impedance.append(avg_impedance)
        electrolyte_resistance.append(row['Re'])
        charge_transfer_resistance.append(row['Rct'])

combined_data = pd.DataFrame({
    'Age': relative_ages,
    'Battery ID': battery_ids,
    'Charge/Discharge Cycle': charge_discharge_cycles,
    'Battery Impedance': battery_impedance,
    'Re (Electrolyte Resistance)': electrolyte_resistance,
    'Rct (Charge Transfer Resistance)': charge_transfer_resistance,
})

fig = go.Figure()

parameters = ["Battery Impedance", "Re (Electrolyte Resistance)", "Rct (Charge Transfer Resistance)"]

for parameter in parameters:
    fig.add_trace(go.Scatter(
        x=[], 
        y=[],  
        mode='markers+lines',
        name=parameter,
        visible=False
    ))

fig.update_layout(
    title="Battery Aging Analysis",
    xaxis_title="Age (Charge/Discharge Cycle)",
    yaxis_title="Parameter Value",
    updatemenus=[
        dict(
            buttons=[dict(label="Select Topic", method="update", args=[{"visible": [False] * len(parameters)}, {"yaxis": {"title": "Select Topic"}}])]
            + [
                dict(label=param,
                     method="update",
                     args=[{"visible": [p == param for p in parameters] + [True] * len(parameters)},
                           {"yaxis": {"title": param}}])
                for param in parameters
            ],
            direction="down",
            showactive=True,
            x=0.15,
            xanchor="left",
            y=1.15,
            yanchor="top"
        ),
        dict(
            buttons=[dict(label="Select Battery ID", method="update", args=[{"x": [], "y": []}, {"title": "Select Battery ID"}])]
            + [
                dict(label=f"Battery {battery_id}",
                     method="update",
                     args=[
                         {
                             "x": [combined_data.loc[combined_data["Battery ID"] == battery_id, "Age"]],
                             "y": [
                                 combined_data.loc[combined_data["Battery ID"] == battery_id, param]
                                 for param in parameters
                             ],
                         },
                         {"title": f"Battery ID {battery_id}"}
                     ])
                for battery_id in combined_data["Battery ID"].unique()
            ],
            direction="down",
            showactive=True,
            x=0.35,
            xanchor="left",
            y=1.15,
            yanchor="top"
        )
    ]
)

fig.write_html("battery_aging_analysis.html")
print("Plot saved. Open 'battery_aging_analysis.html' in a browser.")
