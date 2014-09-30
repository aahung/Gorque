name: this is gorque job name
priority: 1
[
cd ~/particle_diffusion
./simulation_case_5 -o gorque_test/ -n 256 -s 900000
]
[
cd ~/particle_diffusion
./simulation_case_3 -o gorque_test/ -n 256 -s 900000
]
[
cd ~/particle_diffusion
./simulation_case_4 -o gorque_test/ -n 256 -s 900000
]
[
cd ~/particle_diffusion
./simulation_case_1 -o gorque_test/ -n 256 -s 900000
]