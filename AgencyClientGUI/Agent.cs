using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Controls;
using System.Windows.Media.Imaging;

namespace AgencyClientGUI
{
    public class Agent
    {
        public string id { get; set; }
        public string guid { get; set; }
        public bool active { get; set; }
        public string intaddr { get; set; }
        public string extaddr { get; set; }
        public string username { get; set; }
        public string hostname { get; set; }
        public string osinfo { get; set; }
        public int pid { get; set; }
        public string firstcheckin { get; set; }
        public string lastcheckin { get; set; }
        public string intervall { get; set; }
        public string jitter { get; set; }
        public List<Mission> missionlist { get; set; }


        // Add more properties as needed
        public Agent()
        {
            missionlist = new List<Mission>();
        }


    }

    // Method to call when a new agent connects





}
