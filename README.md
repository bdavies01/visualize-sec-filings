# finance

## Scraping data from SEC's Edgar system and visualizing it
Given a ticker of a publicly traded company, retrieve their 10-K (annual) or 10-Q (quarterly) reports and viusalize them using a Sankey diagram. 

WIP: 
- Properly add structured input for a particular ticker
- Companies like banks tend to not get parsed properly
- Still have to manually get segment information (even though the direct link to the table is provided)
    - Segment information tends to be highly variable between companies - hard to design a generic regex or filter to capture segments for all companies
- Fix colors on generated Sankey diagram