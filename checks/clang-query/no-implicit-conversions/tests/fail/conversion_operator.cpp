template<typename Char> struct basic_string_view
{
  basic_string_view(const Char *);// NOLINT(google-explicit-constructor)
};

template<typename Char> struct basic_string
{
  basic_string();
  ~basic_string();
  operator basic_string_view<Char>() const;// NOLINT(google-explicit-constructor)
};

basic_string_view<char> dangling_view()
{
  const basic_string<char> value;
  return value;// expect-finding
}
