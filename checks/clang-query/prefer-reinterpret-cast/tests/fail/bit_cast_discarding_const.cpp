[[nodiscard]] char *mutable_bytes(const int *value)
{
  return (char *)value;// expect-finding
}

[[nodiscard]] void *mutable_address(const int &value)
{
  return (void *)&value;// expect-finding
}
