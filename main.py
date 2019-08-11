import pulp, matplotlib.pyplot as plt, pandas as pd

df=pd.read_csv('DATA.csv')

prices=df['PRICE'].tolist()
power=df['P_WIND'].tolist()


simulation_days=7
step_size=24
opti_horizon=24*2
eta_PEM=0.6
eta_T=0.85
h=3 				#MWh/m3 

r_V_tank=[0]
r_V_in=[0]
r_V_out=[0]
r_revenue=[0]
r_P_grid=[0]
r_P_charge=[0]
r_P_discharge=[0]

for i in range(simulation_days):

	V_tank={}
	V_in={}
	V_out={}
	revenue={}
	P_grid={}
	P_charge={}

	LP = pulp.LpProblem('LP',pulp.LpMaximize)

	for t in range(opti_horizon):

		V_tank[t]=pulp.LpVariable("V_tank_"+str(t), cat=pulp.LpContinuous, upBound=100000, lowBound=0)
		V_in[t]=pulp.LpVariable("V_in_"+str(t), cat=pulp.LpContinuous, lowBound=0)
		V_out[t]=pulp.LpVariable("V_out_"+str(t), cat=pulp.LpContinuous, upBound=30, lowBound=0)
		revenue[t]=pulp.LpVariable("revenue_"+str(t), cat=pulp.LpContinuous, lowBound=0)
		P_grid[t]=pulp.LpVariable("P_grid_"+str(t), cat=pulp.LpContinuous, lowBound=0)
		P_charge[t]=pulp.LpVariable("P_charge_"+str(t), cat=pulp.LpContinuous, lowBound=0)

		if t==0:
			LP += 	V_tank[t]	==	r_V_tank[-1]
			LP += 	V_in[t]		==	r_V_in[-1]
			LP += 	V_out[t]	==	r_V_out[-1]
			LP += 	revenue[t]	==	r_revenue[-1]
			LP += 	P_grid[t]	==	r_P_grid[-1]
			LP += 	P_charge[t]	==	r_P_charge[-1]

		else:
			LP +=	V_tank[t]	== 	V_tank[t-1]	+	V_in[t-1]		-	V_out[t-1]
			LP +=	V_in[t]		== 	P_charge[t]	*	eta_PEM			/	h
			LP +=	revenue[t]	== 	(V_out[t] 	*	h/eta_T			+	P_grid[t])	*	prices[t+i*24]
			LP +=	P_grid[t]	==	V_out[t]*h	+	 power[t+i*24] 	-	P_charge[t]

	LP += sum([revenue[t] for t in range(opti_horizon)])

	status = LP.solve(pulp.solvers.CPLEX_PY(mip=True, msg=False, timeLimit=15, epgap=None))

	print( 'LP status: ' + pulp.LpStatus[status] + '')

	for t in range(step_size):
		r_V_tank.append(V_tank[t].value())
		r_P_grid.append(P_grid[t].value())
		r_P_charge.append(P_charge[t].value())
		r_P_discharge.append(V_out[t].value() 	*	h/eta_T)
'''
fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax1.plot(r_V_tank,	color='r',	label="V_Tank")
ax2.plot(r_P_grid,	color='g',	label="P_grid")
ax2.plot(r_P_charge,color='b',	label="P_charge")
ax2.plot(r_P_discharge,color='y',	label="P_discharge")
ax1.legend(loc="upper left")
ax2.legend(loc="lower left")
plt.show()
'''

df_OUT=pd.DataFrame({'V_Tank':r_V_tank,'P_charge':r_P_charge,'P_discharge':r_P_discharge})

df_OUT.to_csv(r'OUTPUT.csv')