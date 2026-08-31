"""Fictitious presentation data for the visual prototype."""

EMPLOYEES = [
    {"id": 1, "initials": "AM", "name": "Aoife Murphy", "role": "Senior Civil Engineer", "pps": "1234567AA", "status": "Active", "rate": "€38.00", "frequency": "Weekly", "start_date": "12 Feb 2021"},
    {"id": 2, "initials": "LO", "name": "Liam O’Connor", "role": "Structural Engineer", "pps": "2345678BB", "status": "Active", "rate": "€42.00", "frequency": "Weekly", "start_date": "04 Oct 2020"},
    {"id": 3, "initials": "NB", "name": "Niamh Byrne", "role": "Project Engineer", "pps": "3456789CC", "status": "Active", "rate": "€34.50", "frequency": "Weekly", "start_date": "18 Jul 2022"},
    {"id": 4, "initials": "CK", "name": "Cian Kelly", "role": "CAD Technician", "pps": "4567890DD", "status": "Active", "rate": "€31.00", "frequency": "Weekly", "start_date": "06 Mar 2023"},
    {"id": 5, "initials": "SR", "name": "Saoirse Ryan", "role": "Environmental Engineer", "pps": "5678901EE", "status": "Active", "rate": "€36.00", "frequency": "Weekly", "start_date": "22 Jan 2024"},
    {"id": 6, "initials": "DO", "name": "Declan O’Sullivan", "role": "Engineering Manager", "pps": "6789012FF", "status": "On leave", "rate": "€45.00", "frequency": "Weekly", "start_date": "15 May 2019"},
]

PROJECTS = [
    {"name": "Liffey Quays Retrofit", "code": "PRJ-2401", "client": "Dublin City Council", "status": "Active", "employees": 4, "hours": "298.0", "labour": "€11,280.00", "progress": 72},
    {"name": "Cork Harbour Survey", "code": "PRJ-2407", "client": "Port of Cork", "status": "Active", "employees": 3, "hours": "244.0", "labour": "€9,146.00", "progress": 48},
    {"name": "Galway Greenway Design", "code": "PRJ-2412", "client": "Galway County Council", "status": "Review", "employees": 5, "hours": "226.0", "labour": "€8,602.00", "progress": 86},
    {"name": "Drogheda Flood Study", "code": "PRJ-2418", "client": "Louth County Council", "status": "Active", "employees": 3, "hours": "206.0", "labour": "€8,286.00", "progress": 35},
]

TIMESHEETS = [
    {"employee": "Aoife Murphy", "initials": "AM", "project": "Liffey Quays Retrofit", "date": "24 Aug 2026", "regular": "8.0", "overtime": "1.5", "total": "9.5", "status": "Approved"},
    {"employee": "Liam O’Connor", "initials": "LO", "project": "Cork Harbour Survey", "date": "24 Aug 2026", "regular": "8.0", "overtime": "0.0", "total": "8.0", "status": "Approved"},
    {"employee": "Niamh Byrne", "initials": "NB", "project": "Galway Greenway Design", "date": "25 Aug 2026", "regular": "7.5", "overtime": "0.0", "total": "7.5", "status": "Approved"},
    {"employee": "Cian Kelly", "initials": "CK", "project": "Liffey Quays Retrofit", "date": "26 Aug 2026", "regular": "8.0", "overtime": "2.0", "total": "10.0", "status": "Pending"},
    {"employee": "Saoirse Ryan", "initials": "SR", "project": "Drogheda Flood Study", "date": "27 Aug 2026", "regular": "8.0", "overtime": "1.0", "total": "9.0", "status": "Approved"},
    {"employee": "Declan O’Sullivan", "initials": "DO", "project": "Galway Greenway Design", "date": "28 Aug 2026", "regular": "8.0", "overtime": "0.0", "total": "8.0", "status": "Approved"},
]

PAYROLL = [
    {"name": "Aoife Murphy", "initials": "AM", "role": "Senior Civil Engineer", "regular": "160.0", "overtime": "8.0", "rate": "€38.00", "gross": "€6,536.00", "paye": "€1,105.00", "usc": "€261.00", "prsi": "€261.00", "other": "€120.00", "deductions": "€1,747.00", "net": "€4,789.00", "status": "Approved", "pps": "1234567AA"},
    {"name": "Liam O’Connor", "initials": "LO", "role": "Structural Engineer", "regular": "168.0", "overtime": "4.0", "rate": "€42.00", "gross": "€7,308.00", "paye": "€1,320.00", "usc": "€292.00", "prsi": "€292.00", "other": "€85.00", "deductions": "€1,989.00", "net": "€5,319.00", "status": "Approved", "pps": "2345678BB"},
    {"name": "Niamh Byrne", "initials": "NB", "role": "Project Engineer", "regular": "152.0", "overtime": "0.0", "rate": "€34.50", "gross": "€5,244.00", "paye": "€840.00", "usc": "€210.00", "prsi": "€210.00", "other": "€65.00", "deductions": "€1,325.00", "net": "€3,919.00", "status": "Approved", "pps": "3456789CC"},
    {"name": "Cian Kelly", "initials": "CK", "role": "CAD Technician", "regular": "160.0", "overtime": "12.0", "rate": "€31.00", "gross": "€5,518.00", "paye": "€795.00", "usc": "€221.00", "prsi": "€221.00", "other": "€95.00", "deductions": "€1,332.00", "net": "€4,186.00", "status": "Review", "pps": "4567890DD"},
    {"name": "Saoirse Ryan", "initials": "SR", "role": "Environmental Engineer", "regular": "144.0", "overtime": "6.0", "rate": "€36.00", "gross": "€5,508.00", "paye": "€805.00", "usc": "€220.00", "prsi": "€220.00", "other": "€70.00", "deductions": "€1,315.00", "net": "€4,193.00", "status": "Approved", "pps": "5678901EE"},
    {"name": "Declan O’Sullivan", "initials": "DO", "role": "Engineering Manager", "regular": "160.0", "overtime": "0.0", "rate": "€45.00", "gross": "€7,200.00", "paye": "€1,405.00", "usc": "€288.00", "prsi": "€288.00", "other": "€140.00", "deductions": "€2,121.00", "net": "€5,079.00", "status": "Approved", "pps": "6789012FF"},
]

PAYROLL_TOTALS = {
    "gross": "€37,314.00", "deductions": "€9,829.00", "net": "€27,485.00",
    "paye": "€6,270.00", "usc": "€1,492.00", "prsi": "€1,492.00", "other": "€575.00",
}

RECENT_RUNS = [
    {"period": "August 2026", "date": "28 Aug 2026", "employees": 6, "gross": "€37,314.00", "net": "€27,485.00", "status": "Review"},
    {"period": "July 2026", "date": "31 Jul 2026", "employees": 6, "gross": "€36,842.00", "net": "€27,112.00", "status": "Paid"},
    {"period": "June 2026", "date": "30 Jun 2026", "employees": 6, "gross": "€35,990.00", "net": "€26,621.00", "status": "Paid"},
]
