#include <iostream>

void report(const int value)
{
  std::cout << "value:" << std::endl;// expect-finding
  std::cout << value << '\n';
  std::cerr << "done" << std::endl;// expect-finding
}
