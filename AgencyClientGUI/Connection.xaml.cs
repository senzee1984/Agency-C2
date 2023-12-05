using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;

namespace AgencyClientGUI
{
    /// <summary>
    /// Interaction logic for Window1.xaml
    /// </summary>
    public partial class Connection : Window
    {
        public Connection()
        {
            InitializeComponent();
        }

        private void connect(object sender, RoutedEventArgs e)
        {
            // Placeholder for authentication logic
            // You should replace this with actual authentication against a user store
            if (username.Text == "user" && password.Password == "password")
            {
                // Close the Login Window
                //  this.Close();

                // Open the Main Window
                MainWindow mainWindow = new MainWindow(username.Text, password.Password, ipaddr.Text, port.Text);
                mainWindow.Show();
                this.Close();
            }
            else
            {
                MessageBox.Show("Invalid username or password.");
            }
        }
    }
}
