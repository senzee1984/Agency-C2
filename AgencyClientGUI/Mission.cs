using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace AgencyClientGUI
{
    public class Mission
    {
        public string id { get; set; }
        public string spyid { get; set; }
        public string command { get; set; }
        public string output { get; set; }
        public bool iscompleted { get; set; }
        public bool isviewed { get; set; }


        // Add more properties as needed
        public Mission()
        {

        }
    }
}
