Name							GHS Urban Centre Database 2024 - GHS Urban Centre Database 2025	
Dataset ID						GHS_UCDB_R2024	
Version							V1_1	
Data Last Update					30/07/2025	
Alternative name (with version)				GHS Urban Centre Database 2024 - GHS Urban Centre Database 2025, Version 1.1	
Accronym						GHS-UCDB 2025 R2024A V1.1	
Authors							Mari Rivero, Ines; Melchiorri, Michele; Florio, Pietro; Schiavina, Marcello; Goch, Katarzyna; Politis, Panagiotis; Uhl, Johannes H; Pesaresi, Martino; Maffenini, Luca; 
							Sulis, Patrizia; Crippa, Monica; Guizzardi, Diego; Pisoni, Enrico; Belis, Claudio; Jacome Felix Oom, Duarte; Branco, Alfredo; Mwaniki, Dennis; Kochulem, Edwin; Githira, Daniel; 
							Carioli, Alessandra; Ehrlich, Daniele; Tommasi, Pierpaolo; Kemper, Thomas; Dijkstra, Lewis
Document Version					V1.1	
Document Last Update					30/07/2025	
		
Contact point						JRC-GHSL<at>EC.EUROPA.EU	GHSL project related questions
							JRC-GHSL-DATA<at>EC.EUROPA.EU	GHSL data related questions

What's new in V1.1: v1.1 replaces and substitutes v1, which is a deprecated version of the database. Users are encouraged to use v1.1 from the date it 
is released
	Fields update:
	 - GH_BUT_S11_2020, GH_BUT_S12_2020, GH_BUT_S21_2020, GH_BUT_S22_2020, GH_BUT_S23_2020 (recalculated)
	 - GH_BUT_V11_2020, GH_BUT_V12_2020, GH_BUT_V21_2020, GH_BUT_V22_2020, GH_BUT_V23_2020 (recalculated)
	 - GH_BUT_P11_2020, GH_BUT_P12_2020, GH_BUT_P21_2020, GH_BUT_P22_2020, GH_BUT_P23_2020 (recalculated)
	 - SC_SEC_GDP_XXXX (recalculated, fixed bug in the algorithm; calculate total GDP). Current fields: SC_GDP_AVG_XXXX and SC_GDP_SUM_XXXX
 	 - SC_SEC_HDI_XXXX, SC_SEC_GDI_XXXX, SC_SEC_GDF_XXXX, SC_SEC_GDM_XXXX, SC_SEC_LET_XXXX, SC_SEC_LEF_XXXX, SC_SEC_LEM_XXXX, SC_SEC_SET_XXXX,
	   SC_SEC_SEF_XXXX, SC_SEC_SEM_XXXX, SC_SEC_SYT_XXXX, SC_SEC_SYF_XXXX, SC_SEC_SYM_XXXX, SC_SEC_GIF_XXXX, SC_SEC_GIM_XXXX (recalculated, 
	   fixed bug in algorithm)
	 - EX_SHA_POP_XXXX (corrected field name in Index)
	 - EX_Exx_POP_YYYY (corrected field name in Index)
	 - EX_020_S1P_XXXX (corrected field name in tables)
	 - EX_020_S1P_XXXX (corrected field name in tables)
	 - Delete unnamed columns in Exposure tables
	 - SD_LUE_LPR_2000_1990 (corrected field name in tables SD_LUE_LPR_1990_2000)
	 - SD_POP_HGR_XXXX (calculated new population share for UC 2796 years 1895, 1990, 1995, 2025 and UC 572 years 1995, 2000, 2005, 2010)
	 - NS_TPA_NAM_2025_str (corrected field name to NS_TPA_NAM_2025)
	 - NS_TPA_DES_2025_str (corrected field name to NS_TPA_DES_2025)
	 - NS_MPA_NAM_2025_str (corrected field name to NS_MPA_NAM_2025)
	 - NS_MPA_DES_2025_str (corrected field name to NS_MPA_DES_2025)
	 - NS_TPA_PER_2025 (reclaculated, fix bug in algorithm)
	 - NS_MPA_PER_2025 (reclaculated, fix bug in algorithm)
	 - NS_ESB_BIO_XXXX, NS_ESB_GWA_XXXX, NS_ESB_NIT_XXXX, NS_ESB_PHO_XXXX, NS_ESB_P25_XXXX, NS_ESB_SLR_XXXX, NS_ESB_SWA_XXXX, NS_ESB_WET_XXXX
	   NS_ESB_MIN_XXXX, NS_ESB_MAX_XXXX (corrected calculated years in Index)
	 - CL_UTC_T32_XXXX (added variable in Climate tables)
	 - EM_CO2_ENE_XXXX, EM_GHG_ENE_XXXX, EM_NOX_ENE_XXXX, EM_PM2_ENE_XXXX, EM_CO2_RES_XXXX, EM_GHG_RES_XXXX, EM_NOX_RES_XXXX, EM_PM2_RES_XXXX,
	   EM_CO2_IND_XXXX, EM_GHG_IND_XXXX, EM_NOX_IND_XXXX, EM_PM2_IND_XXXX, EM_CO2_TRA_XXXX, EM_GHG_TRA_XXXX, EM_NOX_TRA_XXXX, EM_PM2_TRA_XXXX,
	   EM_CO2_WAS_XXXX, EM_GHG_WAS_XXXX, EM_NOX_WAS_XXXX, EM_PM2_WAS_XXXX, EM_CO2_AGR_XXXX, EM_GHG_AGR_XXXX, EM_NOX_AGR_XXXX, EM_PM2_AGR_XXXX,
	   EM_CO2_TOT_XXXX, EM_GHG_TOT_XXXX, EM_NOX_TOT_XXXX, EM_PM2_TOT_XXXX, EM_CO2_SEN_XXXX, EM_CO2_SRE_XXXX, EM_CO2_SIN_XXXX, EM_CO2_STR_XXXX,
	   EM_CO2_SWA_XXXX, EM_CO2_SAG_XXXX, EM_GHG_SEN_XXXX, EM_GHG_SRE_XXXX, EM_GHG_SIN_XXXX, EM_GHG_STR_XXXX, EM_GHG_SWA_XXXX, EM_GHG_SAG_XXXX,
	   EM_GHG_PER_XXXX, EM_NOX_SEN_XXXX, EM_NOX_SRE_XXXX, EM_NOX_SIN_XXXX, EM_NOX_STR_XXXX, EM_NOX_SWA_XXXX, EM_NOX_SAG_XXXX, EM_PM2_SEN_XXXX,
	   EM_PM2_SRE_XXXX, EM_PM2_SIN_XXXX, EM_PM2_STR_XXXX, EM_PM2_SWA_XXXX, EM_PM2_SAG_XXXX, EM_CO2_PEC_XXXX, EM_GHG_PEC_XXXX, EM_NOX_PEC_XXXX,
	   EM_PM2_PEC_XXXX (reclaculated with new algorithm).
	 - EM_PM2_MOR_XXXX (recalculated only for 2000 and 2020)
	
	Fields removed:
	 - EM_CO2_PER_XXXX, EM_GHG_PER_XXXX, EM_NOX_PER_XXXX, EM_PM2_PER_XXXX, EM_ENE_PER_XXXX, EM_RES_PER_XXXX, EM_IND_PER_XXXX, EM_TRA_PER_XXXX,
	   EM_WAS_PER_XXXX, EM_AGR_PER_XXXX 

	
	
Disclaimer
	" The JRC data are provided ""as is"" and ""as available"" in conformity with the JRC Data Policy1 and the Commission Decision on reuse of Commission documents (2011/833/EU). 
	Although the JRC guarantees its best effort in assuring quality when publishing these data, it provides them without any warranty of warranty of any kind, either express or implied, including, but not limited to, 
	any implied warranty against infringement of third parties' property rights, or merchantability, integration, satisfactory quality and fitness for a particular purpose. The JRC has no obligation to provide technical 
	support or remedies for the data. The JRC does not represent or warrant that the data will be error free or uninterrupted, or that all non-conformities can or will be corrected, or that any data are accurate or complete, 
	or that they are of a satisfactory technical or scientific quality. The JRC or as the case may be the European Commission shall not be held liable for any direct or indirect, incidental, consequential or other damages, 
	including but not limited to the loss of data, loss of profits, or any other financial loss arising from the use of the JRC data, or inability to use them, even if the JRC is notified of the possibility of such damages.
	The designations employed and the presentation of material on this map do not imply the expression of any opinion whatsoever on the part of the European Union concerning the legal status of any country, territory, city or 
	area or of its authorities, or concerning the delimitation of its frontiers or boundaries. Kosovo: This designation is without prejudice to positions on status, and is in line with UNSCR 1244/1999 and the ICJ Opinion on 
	the Kosovo declaration of independence. Palestine: This designation shall not be construed as recognition of a State of Palestine and is without prejudice to the individual positions of the Member States on this issue. "					
				
						
Dataset Citation
	Mari Rivero, Ines; Melchiorri, Michele; Florio, Pietro; Schiavina, Marcello; Goch, Katarzyna; Politis, Panagiotis; Uhl, Johannes H; Pesaresi, Martino; Maffenini, Luca; Sulis, Patrizia; Crippa, Monica; Guizzardi, Diego; 
	Pisoni, Enrico; Belis, Claudio; Jacome Felix Oom, Duarte; Branco, Alfredo; Mwaniki, Dennis; Kochulem, Edwin; Githira, Daniel; Carioli, Alessandra; Ehrlich, Daniele; Tommasi, Pierpaolo; Kemper, Thomas; Dijkstra, Lewis (2024): 
	GHS-UCDB R2024A - GHS Urban Centre Database 2025. European Commission, Joint Research Centre (JRC) [Dataset] doi: 10.2905/1a338be6-7eaf-480c-9664-3a8ade88cbcd PID: http://data.europa.eu/89h/1a338be6-7eaf-480c-9664-3a8ade88cbcd

Related Resources
	Stats in the City – the GHSL Urban Centre Database 2025, MELCHIORRI, M., MARI RIVERO, I., FLORIO, P., SCHIAVINA, M., KRASNODEBSKA, K., POLITIS, P., UHL, J., PESARESI, M., MAFFENINI, L., SULIS, P., CRIPPA, M., GUIZZARDI, D., 
	PISONI, E., BELIS, C., OOM, D., BRANCO, A., MWANIKI, D., GITHIRA, D., KOCHULEM, E., TOMMASI, P., CARIOLI, A., EHRLICH, D., KEMPER, T. and DIJKSTRA, L., Stats in the City – the GHSL Urban Centre Database 2025, 
	Publications Office of the European Union, Luxembourg, 2024, doi:10.2760/3046391 (online),10.2760/5259274 (print), JRC139768.
	
Licence
	European Commission Reuse and Copyright Notice					
	© European Union, 1995-2025					
	Reuse is authorised, provided the source is acknowledged. The reuse policy of the European Commission is implemented by a Decision of 12 December 2011.					
	Disclaimer					
	Unless the following would not be permitted or valid under applicable law, the following applies to the data/information provided by the JRC:					
	The JRC data are provided "as is" and "as available" without warranty of any kind, either express or implied, including, but not limited to, any implied warranty against infringement of third parties' property rights, 
	or merchantability, integration, absence of latent or other defects, satisfactory quality and fitness for a particular purpose. The JRC data do not constitute professional or legal advice (if you need specific advice, 
	you should always consult a suitably qualified professional).					
	The JRC has no obligation to provide technical support or remedies for the data. The JRC does not represent or warrant that the data will be error free or uninterrupted, or that all non-conformities can or will be corrected,
	or that any data are accurate or complete, or that they are of a satisfactory technical or scientific quality.					
	The JRC or as the case may be the European Commission shall not be held liable for any direct or indirect, incidental, consequential or other damages, including but not limited to the loss of data, loss of profits, 
	or any other financial loss arising from the use of the JRC data, or inability to use them, even if the JRC is notified of the possibility of such damages.					
	Decision of 12 December 2011.	