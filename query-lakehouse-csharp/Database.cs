using Microsoft.Data.SqlClient;

namespace TestLakehouseConnection
{
    internal class Database
    {
        private readonly string connectionString = @"Data Source=<lakehouse SQL Connection string>,1433;
                                    Initial Catalog=<Lakehouse name>;
                                    Authentication=ActiveDirectoryPassword;
                                    User Id=<Entra ID>;  
                                    Password=<Entra Password>";

        private readonly SqlConnection conn;

        internal Database()
        {
            Console.WriteLine("Connecting...");
            conn = new SqlConnection(connectionString);
            conn.Open();
        }

        internal void FetchPlayers()
        {
            Console.WriteLine("Fetch list of players...");
            SqlCommand command = new SqlCommand(@"SELECT LastName, FirstName, Wins 
                                                  FROM playerstats 
                                                  WHERE Wins > 0
                                                  ORDER BY Wins DESC", conn);
            using (SqlDataReader reader = command.ExecuteReader())
            {
                while (reader.Read())
                {
                    Console.WriteLine($"{reader["FirstName"]} {reader["LastName"]}\t\t{reader["Wins"]}");
                }

            }
        }
    }
}
