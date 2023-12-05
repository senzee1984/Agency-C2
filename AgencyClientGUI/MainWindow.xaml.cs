using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using System;
using System.Net.Http;
using System.Threading.Tasks;
using System.Reflection;
using Newtonsoft.Json;
using System.Reflection.Emit;
using System.Globalization;
using Newtonsoft.Json.Linq;
using System.Net;
using System.Xml.Linq;
using System.Windows.Threading;


namespace AgencyClientGUI
{

    public partial class MainWindow : Window
    {
        //  List
        List<Agent> agents = new List<Agent>();
        private HashSet<string> knownAgentIds = new HashSet<string>();
       // List<string> agent_ids = new List<string>();
        private Dictionary<string, string> agentOutputs = new Dictionary<string, string>();  //Dict for saving output for each agent tab
        string username;
        string password;
        string ipaddr;
        string port;
        private Point startPoint;
        private bool isDragging = false;
        private const double MaxCanvasWidth = 7800;
        private const double MaxCanvasHeight = 2400;
        private static readonly HttpClient httpClient = new HttpClient();
        private DispatcherTimer timer;

        public MainWindow(string username, string password, string ipaddr, string port)
        {
              
            this.username = username;
            this.password = password;
            this.ipaddr = ipaddr;
            this.port = port;

            string response = GetRequestSynchronously($"http://{ipaddr}:{port}/spies");
            MessageBox.Show("User " + username + " connected to C2 server " + "http://" + ipaddr + ":" + port + "/");


            InitializeComponent();
            UpdateLogArea("User "+username + " connected\n");
            AgentsCanvas.Width = 780;  // Initial Width
            AgentsCanvas.Height = 240;
            InitializeServerIcon();
            agentOutputs.Add("Team Chat", "");

            int initialNumofAgent = 0;
            Random rnd = new Random();

            try
            {
                var agentList = JsonConvert.DeserializeObject<List<Agent>>(response);
                foreach (var agent in agentList)
                {

                    Agent tmpAgent = new Agent();
                    tmpAgent.id = agent.id.ToString();
                    knownAgentIds.Add(tmpAgent.id);
                    tmpAgent.guid = agent.guid;
                    tmpAgent.username = agent.username;
                    tmpAgent.hostname = agent.hostname;
                    tmpAgent.pid = agent.pid;
                    tmpAgent.lastcheckin = agent.lastcheckin;
                    tmpAgent.firstcheckin = agent.firstcheckin;
                    tmpAgent.extaddr = agent.extaddr;
                    tmpAgent.intaddr = agent.intaddr;
                    agents.Add(tmpAgent);   //Add current agent to a list
                    InitializeAgentIcon(tmpAgent, rnd.Next(20,750), rnd.Next(20,210));     //Set random (x,y) for the agent icon
                    agentOutputs.Add(tmpAgent.id.ToString(), "");
                }
                UpdateLogArea(agents.Count.ToString() + " spy(ies) alive\n");  //Add log info about initial agent
            }
            catch (Exception ex)
            {
                Console.WriteLine("Error during JSON parsing: " + ex.Message);
            }

            timer = new DispatcherTimer();
            timer.Interval = TimeSpan.FromSeconds(1);
            timer.Tick += async (sender, e) => await StartPollingAllAgents();
            timer.Start();








        }

        private void UpdateLogArea(string log)  //Update log area in specified format
        {
            logArea.Text += "[+] "+DateTime.Now.ToString() + "  " + log;
        }

        private void UpdateInteractionArea(string agentid, string log)  //Update log area in specified format
        {
            interactionTextArea.Text += "[+] " + DateTime.Now.ToString() + "  " + log+"\n";
            agentOutputs[agentid] += "[+] " + DateTime.Now.ToString() + "  " + log+"\n";
        }

        private string GetRequestSynchronously(string uri)  //Send a GET request to a supplied URL
        {
            using (var client = new HttpClient())
            {
                client.Timeout = TimeSpan.FromSeconds(5);

                try
                {
                    var request = new HttpRequestMessage(HttpMethod.Get, uri);
                    var response = client.Send(request); // Synchronous call
                    if (response.IsSuccessStatusCode)
                    {
                        return response.Content.ReadAsStringAsync().Result;
                    }
                    else
                    {
                        return $"Error: {response.StatusCode}";
                    }
                }
                catch (TaskCanceledException)
                {
                    MessageBox.Show("Connection failed");
                    return "Connection failed";
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Exception occured");
                    return $"Error: {ex.Message}";
                }
            }
        }











        private void InitializeServerIcon() //Draw the server icon as long as the connection established
        {

            Image serverIcon = new Image
            {
                Width = 60, 
                Height = 60, 
                Source = new BitmapImage(new Uri("Resources\\server.png", UriKind.Relative)) // Path to the server icon image
            };

            // Set the position on the canvas
            Canvas.SetLeft(serverIcon, 10); 
            Canvas.SetTop(serverIcon, 80);  

            serverIcon.MouseDown += Icon_MouseDown;
            serverIcon.MouseMove += Icon_MouseMove;
            serverIcon.MouseUp += Icon_MouseUp;

            // Add the server icon to the canvas
            AgentsCanvas.Children.Add(serverIcon);

            System.Windows.Controls.Label serverLabel = new System.Windows.Controls.Label
            {
                Content = "Agency",
                Foreground = Brushes.White, // Set text color
                Background = Brushes.Transparent, // Set background color
                Width = 60 // Ensure it aligns with the width of the icon
            };

            // Position the label below the icon
            Canvas.SetLeft(serverLabel, 10);
            Canvas.SetTop(serverLabel, 80 + serverIcon.Height);

            // Add the label to the canvas
            AgentsCanvas.Children.Add(serverLabel);
            serverIcon.Tag = serverLabel;

            // Link the label to the icon for moving together
            double fromX = 10 + (serverIcon.Width / 2);
            double fromY = 80 + (serverIcon.Height / 2);

            // Server icon's center position (adjust these values based on your server icon's position)
            double toX = fromX; // Assuming server icon center is at (40, 120)
            double toY = fromY;
            Line arrow = DrawArrow(fromX, fromY, toX, toY);

            serverIcon.Tag = new { Label = serverLabel, Arrow = arrow };

        }


        private void Icon_MouseDown(object sender, MouseButtonEventArgs e)  //When an icon is clicked
        {
            if (e.ChangedButton == MouseButton.Left || e.ChangedButton == MouseButton.Right  )
            {
                isDragging = true;
                var icon = (Image)sender;
                startPoint = e.GetPosition(AgentsCanvas);
                icon.CaptureMouse();
                icon.Opacity = 0.7; 
            }
        }

        private void Icon_MouseMove(object sender, MouseEventArgs e)
        {
            if (isDragging && e.LeftButton == MouseButtonState.Pressed)
            {
                var icon = (Image)sender;
                var tag = (dynamic)icon.Tag;
                var label = tag.Label as System.Windows.Controls.Label;
                var arrow = tag.Arrow as Line;

                var position = e.GetPosition(AgentsCanvas);
                var offset = position - startPoint;
                startPoint = position;

                double newLeft = Canvas.GetLeft(icon) + offset.X;
                double newTop = Canvas.GetTop(icon) + offset.Y;

                // Update icon position
                Canvas.SetLeft(icon, newLeft);
                Canvas.SetTop(icon, newTop);

                // Update label position
                Canvas.SetLeft(label, newLeft);
                Canvas.SetTop(label, newTop + icon.Height);

                // Check if the moved icon is the server icon
                if (icon.Source.ToString().Contains("server.png")) // Check if the icon is the server icon
                {
                    // Update all agent arrows to point to the new server location
                    foreach (var child in AgentsCanvas.Children)
                    {
                        if (child is Image agentIcon && agentIcon.Source.ToString().Contains("spy.png")) // Check if the child is an agent icon
                        {
                            var agentTag = (dynamic)agentIcon.Tag;
                            var agentArrow = agentTag.Arrow as Line;
                            if (agentArrow != null)
                            {
                                // Update the arrow's end point to the new server position
                                agentArrow.X2 = newLeft + (icon.Width / 2);
                                agentArrow.Y2 = newTop + (icon.Height / 2);
                            }
                        }
                    }
                }
                else if (arrow != null) // If the icon is not the server, update its arrow normally
                {
                    // Update arrow position
                    arrow.X1 = newLeft + (icon.Width / 2);
                    arrow.Y1 = newTop + (icon.Height / 2);
                }

                UpdateCanvasSize(newLeft + icon.Width, newTop + icon.Height);
            }
        }

        private void Icon_MouseUp(object sender, MouseButtonEventArgs e)    //When the click is released
        {
            isDragging = false;
            var icon = (Image)sender;
            icon.ReleaseMouseCapture();
            icon.Opacity = 1.0; 
        }

        private void UpdateCanvasSize(double newWidth, double newHeight)    //If the icon is out of original area, adjust the size
        {
            AgentsCanvas.Width = Math.Min(MaxCanvasWidth, Math.Max(AgentsCanvas.Width, newWidth));
            AgentsCanvas.Height = Math.Min(MaxCanvasHeight, Math.Max(AgentsCanvas.Height, newHeight));
        }
















        // Draw a new agent icon when a new agent is connected
        private void OnNewAgentConnected(string id)
        {
            Agent newAgent = new Agent();
            newAgent.id = id;
            InitializeAgentIcon(newAgent, 10, 10); 
        }

        public void InitializeAgentIcon(Agent tmpAgent, double x, double y)
        {
            Image agentIcon = new Image
            {
                Width = 75,
                Height = 75, 
                Source = new BitmapImage(new Uri("Resources\\spy.png", UriKind.Relative)) 
            };


            Canvas.SetLeft(agentIcon, x);
            Canvas.SetTop(agentIcon, y);

            agentIcon.MouseDown += Icon_MouseDown;
            agentIcon.MouseMove += Icon_MouseMove;
            agentIcon.MouseUp += Icon_MouseUp;

            // Create a context menu for the agent icon
            ContextMenu contextMenu = new ContextMenu();

            // Create menu items
            MenuItem interactItem = new MenuItem { Header = "Interact" };
            MenuItem exitItem = new MenuItem { Header = "Exit" };

            // Add click event handlers for the menu items
            interactItem.Click += (sender, e) => InteractItem_Click(sender, e, tmpAgent);
            exitItem.Click += ExitItem_Click;

            // Add menu items to the context menu
            contextMenu.Items.Add(interactItem);
            contextMenu.Items.Add(exitItem);

            // Assign the context menu to the agent icon
            agentIcon.ContextMenu = contextMenu;

            // Add the icon to the canvas
            AgentsCanvas.Children.Add(agentIcon);

            System.Windows.Controls.Label agentLabel = new System.Windows.Controls.Label
            {
                Content = tmpAgent.id.ToString() + "@" + tmpAgent.hostname + "\\" + tmpAgent.username + "@" + tmpAgent.pid.ToString(),
                Foreground = Brushes.White, 
                Background = Brushes.Transparent, 
                Width = 75 
            };

            // Position the label below the icon
            Canvas.SetLeft(agentLabel, x);
            Canvas.SetTop(agentLabel, y + agentIcon.Height);

            // Add the label to the canvas
            AgentsCanvas.Children.Add(agentLabel);

            // Link the label to the icon for moving together
            agentIcon.Tag = agentLabel;

            double fromX = x + (agentIcon.Width / 2);
            double fromY = y + (agentIcon.Height / 2);

            // Server icon's center position (adjust these values based on the server icon's position)
            double toX = 40; // Assuming server icon center is at (40, 120)
            double toY = 120;

            Line arrow = DrawArrow(fromX, fromY, toX, toY);
            AgentsCanvas.Children.Add(arrow);

            // Store the arrow in the Tag property with the label for easy access
            agentIcon.Tag = new { Label = agentLabel, Arrow = arrow };

        }


        private Line DrawArrow(double fromX, double fromY, double toX, double toY)
        {
            Line arrow = new Line
            {
                Stroke = Brushes.Green,
                StrokeThickness = 2,
                X1 = fromX,
                Y1 = fromY,
                X2 = toX,
                Y2 = toY,
                Tag = "arrow" // Tag to identify arrows
            };


            return arrow;
        }





        private void InteractItem_Click(object sender, RoutedEventArgs e, Agent agent)
        {
            // Iterate through existing tabs to check if a tab for this agent already exists
            foreach (TabItem tab in AgentTabControl.Items)
            {
                var headerStackPanel = tab.Header as StackPanel;
                if (headerStackPanel != null)
                {
                    var textBlock = headerStackPanel.Children.OfType<TextBlock>().FirstOrDefault();
                    if (textBlock != null && textBlock.Text == (agent.id + "#" + agent.hostname + "\\" + agent.username))
                    {
                        // Tab for this agent already exists, so just focus it and return
                        AgentTabControl.SelectedItem = tab;
                        interactionTextArea.Text = agentOutputs[agent.id.ToString()];
                        return;
                    }
                }
            }

            // If no existing tab is found for this agent, add a new one
            AddNewAgentTab(agent);
        }

        private void AddNewAgentTab(Agent agent)
        {
            TabItem newTab = CreateTabItemWithCloseButton(agent.id+"#"+agent.hostname+"\\"+agent.username);    //Create a new tab item with X button
            AgentTabControl.SelectedItem = newTab;
            CurrentAgentInfo.Content = agent.id.ToString()+":"+agent.hostname+"\\"+agent.username+"@"+agent.pid.ToString();
        }

        private void AgentTabControl_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            // Check if the sender is indeed a TabControl and it has a selected item
            if (sender is TabControl tabControl && tabControl.SelectedItem is TabItem selectedTab)
            {
                string tabAgentID = "";
                // Check if the tab header is a string (for pre-added tabs)
                if (selectedTab.Header is string headerText)
                {
                    tabAgentID = headerText;
                }
                // Check if the tab header is a StackPanel (for dynamically added tabs)
                else if (selectedTab.Header is StackPanel headerStackPanel)
                {
                    var textBlock = headerStackPanel.Children.OfType<TextBlock>().FirstOrDefault();
                    if (textBlock != null)
                    {
                        tabAgentID = textBlock.Text.Split('#')[0];
                    }
                }

                if (tabAgentID != "Team Chat")
                {
                    // Update the CurrentAgentInfo label's content
                    foreach (Agent agent in agents)
                    {
                        if (agent.id.ToString() == tabAgentID)
                        {
                            CurrentAgentInfo.Content = agent.id.ToString() + ":" + agent.hostname + "\\" + agent.username + "@" + agent.pid.ToString();
                            break;
                        }
                    }

                    // Update the interactionTextArea's content
                    if (agentOutputs.ContainsKey(tabAgentID))
                    {
                        interactionTextArea.Text = agentOutputs[tabAgentID];
                    }
                    else
                    {
                        // Handle the case where the tabAgentID is not found in agentOutputs (e.g., "Team Chat")
                        interactionTextArea.Text = "";
                    }
                }
                else
                {
                    CurrentAgentInfo.Content = "Select a spy to interact";
                    interactionTextArea.Text = agentOutputs[tabAgentID];
                }
            }
        }


        private void ExitItem_Click(object sender, RoutedEventArgs e)
        {
            // Implement exit logic here
        }



        private TabItem CreateTabItemWithCloseButton(string tabAgentInfo)
        {
            // Create the tab item
            TabItem tabItem = new TabItem();
            AgentTabControl.Items.Add(tabItem);

            // Create a stack panel with text and a close button
            StackPanel stackPanel = new StackPanel { Orientation = Orientation.Horizontal };
            TextBlock text = new TextBlock { Text = tabAgentInfo, Margin = new Thickness(0, 0, 5, 0) };
            Button closeButton = new Button { Content = "X", Padding=new System.Windows.Thickness(0), FontSize = 10,Width = 15, Height = 15, Margin = new Thickness(0, 0, 0, 0) };
            closeButton.Click += (s, e) =>
            {
                AgentTabControl.Items.Remove(tabItem);
                CurrentAgentInfo.Content = "Select a spy";
            };

            stackPanel.Children.Add(text);
            stackPanel.Children.Add(closeButton);

            // Set the stack panel as the header of the tab
            tabItem.Header = stackPanel;

            return tabItem;
        }

        public void UpdateAgentOutput(string id, string newOutput)
        {
            if (agentOutputs.ContainsKey(id))
            {
                agentOutputs[id] += newOutput;
            }
        }








        private async void InputTextBox_KeyDown(object sender, KeyEventArgs e)    //Send a command by hitting Enter key
        {
            if (e.Key == Key.Enter)
            {
                // Get the text from the TextBox
                TextBox inputTextBox = sender as TextBox;
                string inputText = inputTextBox.Text;

                if (AgentTabControl.SelectedItem is TabItem selectedTab)
                {
                    string agentId = "";

                    if (selectedTab.Header is StackPanel headerStackPanel)
                    {
                        var tabText = headerStackPanel.Children.OfType<TextBlock>().FirstOrDefault().Text;
                        agentId = tabText.Split('#')[0];
                        await SendTask(inputText, agentId);
                    }
                    else if (selectedTab.Header is string headerText && headerText == "Team Chat")
                    {
                        await SendTask("User sent message: " + inputText, "Team Chat");
                    }

                    // Clear the TextBox
                    inputTextBox.Clear();
                }
            }
        }


        private async Task SendTask(string input, string agentId) // Handle the command
        {
            if (string.IsNullOrWhiteSpace(input))
                return;

            if (input.Contains("Mission assigned: cls"))
            {
                interactionTextArea.Text = "";
                UpdateAgentOutput(agentId, "");
            }
            else
            {
                string serverUrl = $"http://localhost:8000/mission/{agentId}";
                var commandJson = new StringContent(JsonConvert.SerializeObject(new { command = input }), Encoding.UTF8, "application/json");

                try
                {
                    var response = await httpClient.PostAsync(serverUrl, commandJson);
                    response.EnsureSuccessStatusCode();

                    string responseBody = await response.Content.ReadAsStringAsync();
                    // Process the response if necessary

                    UpdateInteractionArea(agentId, input);
                }
                catch (HttpRequestException e)
                {
                    // Handle error, maybe log the exception or show a message to the user
                    Console.WriteLine($"Error sending command: {e.Message}");
                }
            }
        }

        public async Task<List<Agent>> GetAllAgents()
        {
            string serverUrl = "http://localhost:8000/spies";
            try
            {
                HttpResponseMessage response = await httpClient.GetAsync(serverUrl);
                response.EnsureSuccessStatusCode();
                string responseBody = await response.Content.ReadAsStringAsync();
                List<Agent> agents = JsonConvert.DeserializeObject<List<Agent>>(responseBody);
                return agents;
            }
            catch (HttpRequestException e)
            {
                // Handle exception
                // Optionally return an empty list or null depending on how you want to handle errors
                return new List<Agent>();
            }
        }

        private async Task  StartPollingAllAgents()
        {
            while (true)
            {
                await Task.Delay(1000); // Wait for 1 second
                var agents = await GetAllAgents();

                foreach (var agent in agents)
                {
                    if (knownAgentIds.Add(agent.id)) // Add returns true if the element is new
                    {
                        Dispatcher.Invoke(() =>
                        {
                            OnNewAgentConnected(agent.id);
                        });
                    }

                    foreach (var mission in agent.missionlist)
                    {
                        if ( mission.iscompleted == true && mission.isviewed == false)
                        {
                            string output = await GetOutputFromServer(agent.id, mission.id);
                            agentOutputs[agent.id] += (agentOutputs.ContainsKey(agent.id) ? agentOutputs[agent.id] : "") + output;
                            interactionTextArea.Text += (agentOutputs.ContainsKey(agent.id) ? agentOutputs[agent.id] : "") + output;
                            mission.isviewed = true;
                           // MessageBox.Show(output);
                        }
                        
                    }
                }
            }
        }


        public async Task<string> GetOutputFromServer(string agentid, string missionid)
        {
            string serverUrl = $"http://localhost:8000/spy/{agentid}/{missionid}/output";
            try
            {
                HttpResponseMessage response = await httpClient.GetAsync(serverUrl);
                response.EnsureSuccessStatusCode();
                return await response.Content.ReadAsStringAsync();
            }
            catch (HttpRequestException e)
            {
                // Handle exception
                return $"Error: {e.Message}";
            }
        }




    }



}