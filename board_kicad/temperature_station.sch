EESchema Schematic File Version 4
EELAYER 30 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title ""
Date ""
Rev ""
Comp ""
Comment1 ""
Comment2 ""
Comment3 ""
Comment4 ""
$EndDescr
$Comp
L MCU_Module:WeMos_D1_mini U1
U 1 1 60086523
P 4500 3900
F 0 "U1" H 4500 3011 50  0000 C CNN
F 1 "WeMos_D1_mini" H 4500 2920 50  0000 C CNN
F 2 "Module:WEMOS_D1_mini_light" H 4500 2750 50  0001 C CNN
F 3 "https://wiki.wemos.cc/products:d1:d1_mini#documentation" H 2650 2750 50  0001 C CNN
	1    4500 3900
	1    0    0    -1  
$EndComp
$Comp
L Sensor:DHT11 U2
U 1 1 600874FD
P 5850 3700
F 0 "U2" H 5606 3746 50  0000 R CNN
F 1 "DHT22" H 5606 3655 50  0000 R CNN
F 2 "Sensor:Aosong_DHT11_5.5x12.0_P2.54mm" H 5850 3300 50  0001 C CNN
F 3 "http://akizukidenshi.com/download/ds/aosong/DHT11.pdf" H 6000 3950 50  0001 C CNN
	1    5850 3700
	-1   0    0    -1  
$EndComp
Wire Wire Line
	5850 3400 5850 2950
Wire Wire Line
	5850 2950 5300 2950
Wire Wire Line
	4600 2950 4600 3100
Wire Wire Line
	4500 4850 4500 4700
Wire Wire Line
	4100 3500 4000 3500
Wire Wire Line
	4000 3500 4000 2850
Wire Wire Line
	4000 2850 5050 2850
Wire Wire Line
	5050 2850 5050 3500
Wire Wire Line
	5050 3500 4900 3500
NoConn ~ 4100 3900
NoConn ~ 4100 3800
NoConn ~ 4900 4300
NoConn ~ 4900 4200
NoConn ~ 4900 4100
NoConn ~ 4900 4000
NoConn ~ 4900 3800
NoConn ~ 4900 3650
NoConn ~ 4900 3400
$Comp
L Device:R R1
U 1 1 60089549
P 5300 3250
F 0 "R1" H 5370 3296 50  0000 L CNN
F 1 "10K" H 5370 3205 50  0000 L CNN
F 2 "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal" V 5230 3250 50  0001 C CNN
F 3 "~" H 5300 3250 50  0001 C CNN
	1    5300 3250
	1    0    0    -1  
$EndComp
Wire Wire Line
	5300 3100 5300 2950
Connection ~ 5300 2950
Wire Wire Line
	5300 2950 4600 2950
NoConn ~ 4900 3600
NoConn ~ 4400 3100
Wire Wire Line
	4500 4850 5850 4850
Wire Wire Line
	5850 4850 5850 4000
Wire Wire Line
	5550 3700 5300 3700
Wire Wire Line
	5300 3400 5300 3700
Connection ~ 5300 3700
Wire Wire Line
	5300 3700 4900 3700
NoConn ~ 4900 3900
$EndSCHEMATC
