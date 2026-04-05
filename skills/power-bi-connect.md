# Skill: Connect to Power BI Desktop

## Trigger
Activate when the user wants to connect to Power BI Desktop, mentions "connect", "pbi connect", "local instance", "no connection", or cannot run DAX/model commands.

## Steps
1. Make sure Power BI Desktop is open with a .pbix file
2. Run: `pbi-agent connect --list` to see open instances
3. Run: `pbi-agent connect` to connect to the first detected instance
4. Run: `pbi-agent doctor` to diagnose if connection fails

## Common Issues
- **No instances found**: Power BI Desktop not open, or open without a file loaded
- **pythonnet error**: Run `pip install powerbi-agent[desktop]`
- **Port in use**: Use `pbi-agent connect --port <port>` to specify manually
