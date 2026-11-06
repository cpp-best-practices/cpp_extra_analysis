void take_double(double);
void take_long_long(long long);

void promote_arguments(const float single, const int integer)
{
  take_double(single);// expect-finding
  take_double(integer);// expect-finding
  take_long_long(integer);// expect-finding
  take_double(1.3f);// expect-finding
  take_double(1);// expect-finding
}
