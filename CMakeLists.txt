cmake_minimum_required(VERSION 2.8.3)
project(rossock)

find_package(catkin REQUIRED)

catkin_python_setup()

catkin_package()

install(PROGRAMS
  scripts/rossock_client_tcp.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(FILES
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
