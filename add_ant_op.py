import os

import pyaedt
import tempfile
import numpy as np
import random

# Use the 2023R2 release of HFSS.

non_graphical = False  # Set to False to launch the AEDT UI.
desktop_version = "2023.1"
length_units = "mm"
freq_units = "GHz"


tmpdir = tempfile.TemporaryDirectory(suffix="_aedt")
project_folder = tmpdir.name
Antenna = os.path.join(project_folder, "antenna")

# 初始化EDA算法的参数分布
def initialize_parameter_distribution():
    # 假设L0和L1的起始分布均匀分布
    L0_distribution = np.linspace(27.5, 28.1, 100)
    L1_distribution = np.linspace(6.5, 7.5, 100)
    return L0_distribution, L1_distribution

# 生成参数
def generate_parameters(L0_distribution, L1_distribution):
    L0 = np.random.choice(L0_distribution)
    L1 = np.random.choice(L1_distribution)
    return L0, L1

# 更新参数分布
def update_distribution(selected_parameters):
    new_L0_distribution = np.percentile(selected_parameters['L0'], [10, 90])  # 选择10%到90%分位数作为新范围
    new_L1_distribution = np.percentile(selected_parameters['L1'], [10, 90])
    return np.linspace(new_L0_distribution[0], new_L0_distribution[1], 100), \
           np.linspace(new_L1_distribution[0], new_L1_distribution[1], 100)


def main():

    # Launch HFSS
    # -----------
    hfss = pyaedt.Hfss(projectname=Antenna,
                       solution_type="Driven Modal",
                       #designname="patch",
                       non_graphical=non_graphical,
                       specified_version=desktop_version)
    hfss.modeler.model_units = length_units
    hfss["H"] = "1.6mm"
    hfss["L0"] = "28mm"
    hfss["W0"] = "37.26mm"
    hfss["L1"] = "7mm"
    hfss["Length"] = "30.6mm"
    l0_distribution, l1_distribution = initialize_parameter_distribution()

    # model
    box1 = hfss.modeler.create_box(["-L0", "-W0", 0], ["2*L0", "2*W0", "H"], name="Substrate", matname="FR4_epoxy")
    rectangle = hfss.modeler.create_rectangle(csPlane="XY", position=["-L0/2", "-W0/2", "H"], dimension_list=["W0", "L0"], name="Patch")
    rectangle1 = hfss.modeler.create_rectangle(csPlane="XY", position=["-L0", "-W0", "0"], dimension_list=["2*L0", "2*W0"], name="Gnd")
    cylinder = hfss.modeler.create_cylinder(cs_axis="Z", position=["L1", "0", "0"], radius=0.6, height = "H", numSides=0, name="Feed", matname="pec")
    circle = hfss.modeler.create_circle(cs_plane="XY", position=["L1", "0", "0"], radius=1.5, name="Port")
    hfss.modeler.subtract(blank_list=rectangle1, tool_list=[circle], keep_originals=True,)

    # Set boundary conditions and incentives
    perfe1 = hfss.assign_perfecte_to_sheets("Patch", sourcename=None, is_infinite_gnd=False)
    perfe2 = hfss.assign_perfecte_to_sheets("Gnd", sourcename=None, is_infinite_gnd=False)

    # Set radiation boundary conditions
    box2 = hfss.modeler.create_box(["-(L0/2+Length)", "-(W0/2+Length)", "-Length"], ["L0+2*Length", "W0+2*Length", "H+2*Length"], name="Airbox", matname="FR4_epoxy")
    box_faces = box2.faces
    hfss.assign_radiation_boundary_to_faces(box_faces, boundary_name='Rad1')

    hfss.lumped_port("Port",  create_port_sheet=False, port_on_plane=True,
                     integration_line=[[7.2, -1.4, 0], [6.8, 1.4, 0 ]], impedance=50, name="1")

    l0_distribution, l1_distribution = initialize_parameter_distribution()

    # Solve settings
    setup = hfss.create_setup("MySetup")
    setup.props["Frequency"] = "2.45GHz"
    setup.props["MaximumPasses"] = 20
    setup1 = hfss.create_linear_step_sweep(
        setupname=setup.name,
        unit="GHz",
        freqstart=1.5,
        freqstop=3.5,
        step_size=0.01,
        sweepname="sweep1",
        sweep_type="Fast",
        save_fields=False,
    )
    variations = hfss.available_variations.nominal_w_values_dict
    variations["Theta"] = ["All"]
    variations["Phi"] = ["All"]
    variations["Freq"] = ["3.3GHz"]
    for i in range(10):
        L0, L1 = np.random.choice(l0_distribution), np.random.choice(l1_distribution)
        hfss["var_L0"] = L0
        hfss["var_L1"] = L1
        hfss.analyze_setup("MySetup")
        s11 = hfss.post.get_solution_data("dB(S(1,1))",
                                          plot_type="Rectangular Plot",
                                          primary_sweep_variable="Freq",
                                          report_category="S-Parameters",
                                          variations=variations,
                                           )

        print(f"Iteration {i + 1}: L0={L0} mm, S(1,1)={s11}")


        #print(s11.solutions)







        hfss.release_desktop()
        tmpdir.cleanup()

if __name__ == "__main__":
    main()































