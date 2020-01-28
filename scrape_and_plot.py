from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import re
import pandas as pd
import time
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

# GRABBING INFO
options = webdriver.ChromeOptions()
#options.add_argument('--headless')
browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
browser.get('https://firststop.sos.nd.gov/search/business')
# search "X"
browser.find_element_by_css_selector('input.search-input[placeholder="Search by name or system id (###-#####)"]').send_keys("X")
# click "advanced" button
browser.find_element_by_class_name('advanced-search-toggle').click()
time.sleep(0.8)
# select "starts with"
browser.find_elements_by_css_selector('.radio-label')[1].click()
# Active entities only
browser.find_element_by_class_name('checkbox-box[for="field-ACTIVE_ONLY_YN"]').click()
# search button
browser.find_element_by_class_name('btn.btn-primary.btn-raised').click()
time.sleep(0.8)
# expand button
button_expand = browser.find_elements_by_class_name('icon.icon-caret-right')
# make empty lists for values
company_name_list = []
agent_list = []
agent_info_list = []
browser.execute_script("window.scrollTo(0, 1600)")

# loop through the table
for i, val in enumerate(button_expand, start=0):
    if i == 193:
        break
    add = i*65.5
    browser.execute_script("window.scrollTo(0, {})".format(int(add)))
    time.sleep(0.7)
    val.click()
    # get company name - skip if it doesnt start with "X"
    company_name = browser.find_element_by_css_selector('h4').text
    if company_name.startswith("X") == False:
        continue
    time.sleep(1)
    # get table info
    table_text = browser.find_element_by_class_name('inner-drawer').text
    table_text = table_text.replace("\n", " ")
    #print(table_text)
    # Find agents of interest and only take that string
    pattern = "(?=Registered Agent |Owner Name |Commercial Registered Agent |Owners ).+(?= View History| Nature)"
    new_string = re.compile(pattern).findall(table_text)[0]
    #print(table_text)
    if " Nature of Business " in new_string:
        new_string = re.compile(".+(?= Nature)").findall(new_string)[0]
    #split string into two parts - agent info and contact info
    new_string = re.split("(?<=Agent )|(?<=Owner Name )|(?<=Owners )", new_string)
    #print(new_string)
    if " Owner Address " in new_string[1]:
        new_string[1] = re.sub("Owner Address", "", new_string[1])
    # add data into separate lists
    agent_list.append(new_string[0])
    agent_info_list.append(new_string[1])
    company_name_list.append(company_name)

# save as df and write to .csv
df = pd.DataFrame(data = {'company': np.array(company_name_list), 'agent': np.array(agent_list), 'agent_info': np.array(agent_info_list)})
#df.to_csv('company_networks.csv', index=False)

# NETWORKX PLOTTING - using "http://jonathansoma.com/lede/algorithms-2017/classes/networks/networkx-graphs-from-source-target-dataframe/" as a guide
#df = pd.read_csv("company_networks.csv")
G = nx.from_pandas_edgelist(df, source='company', target='agent_info')

# layout
plt.figure(figsize=(8,8))
layout = nx.spring_layout(G, iterations=250, k =.6)
nx.draw_networkx_edges(G, layout, edge_color='#AAAAAA')

# number of connections and weights for agents
agents = [node for node in G.nodes() if node in df.agent_info.unique()]
agent_size = [G.degree(node)*150 for node in G.nodes() if node in df.agent_info.unique()]

# assuming companies sufficiently unique
companies = [node for node in G.nodes() if node in df.company.unique()]
nx.draw_networkx_nodes(G, layout, nodelist = companies, node_color='#AAAAAA', node_size=50)

nx.draw_networkx_nodes(G, layout, nodelist=agents, node_size=agent_size, node_color='lightblue')
print(agent_size)


# drawing popular agents and add their labels
popular_agents = [node for node in G.nodes() if node in df.agent_info.unique() and G.degree(node) > 1]
abbrv_agents = []
for n in popular_agents:
    a = n[:15]
    abbrv_agents.append(a)
#nx.draw_networkx_nodes(G, layout, nodelist=popular_agents, node_color="orange", node_size = agent_size)
popular_agents_labels = dict(zip(popular_agents, abbrv_agents))
nx.draw_networkx_labels(G,layout, labels=popular_agents_labels, font_size=8)

# company labels
#node_labels = dict(zip(companies,companies))
#nx.draw_networkx_labels(G, layout, labels=node_labels, font_size=6, alpha=0.5)

# plotting
plt.title('Frequently Appearing Agents/Owners')
plt.axis('off')
plt.show()