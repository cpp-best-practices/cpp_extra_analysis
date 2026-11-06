struct string
{
};

struct istream
{
  explicit operator bool() const;
  ~istream();
};

istream &getline(istream &input, string &output);

void read_lines()
{
  istream input;
  string output;

  while (getline(input, output)) {// expect-finding
  }
}
