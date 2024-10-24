# Linac Wire Scan Basic
Uses AcSys Python to execute a fast wire scan by issuing one setpoint and collecting data.  

- make the beta calculation more efficient & just calculate beta/gamma/etc. from the energy, rather than making it be provided

Can run one WS or a QS. 

1/17/2023 Changes that were made from the previous version (1/3/2024):  
- added an optional string that can be put into the log file  
- changed the data acquisition to acquire on the $0A  

# To Do
- do we have to be concerned about running two WSs in the quad scan when the wire scanners are impinging on beam? 