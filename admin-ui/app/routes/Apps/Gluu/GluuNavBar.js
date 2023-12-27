import React, { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import {
  Avatar,
  AvatarAddOn,
  DropdownToggle,
  Navbar,
  Nav,
  NavItem,
  Notifications,
  SidebarTrigger,
  ThemeSetting,
  UncontrolledDropdown,
} from 'Components'
import { LanguageMenu } from './LanguageMenu'
import { useSelector } from 'react-redux'
import { DropdownProfile } from 'Routes/components/Dropdowns/DropdownProfile'
import { randomAvatar } from '../../../utilities'
import { ErrorBoundary } from 'react-error-boundary'
import GluuErrorFallBack from './GluuErrorFallBack'

function GluuNavBar() {
  const userInfo = useSelector((state) => state.authReducer.userinfo)
  const [showCollapse, setShowCollapse] = useState(
    window.matchMedia('(max-width: 768px)').matches,
  )
  useEffect(() => {
    window
      .matchMedia('(max-width: 768px)')
      .addEventListener('change', (e) => setShowCollapse(e.matches))
  }, [])
  return (
    <ErrorBoundary FallbackComponent={GluuErrorFallBack}>
      <Navbar expand="lg" themed>
        <Nav>
          {showCollapse && (
            <NavItem>
              <SidebarTrigger id="navToggleBtn" />
            </NavItem>
          )}
        </Nav>
        <Box display="flex" justifyContent="space-between" width="100%">
          <h3 className="page-title" id="page-title">Dashboard</h3>
          <Nav className="ms-auto" pills>
            <Notifications />
            <LanguageMenu userInfo={userInfo} />
            <ThemeSetting userInfo={userInfo} />
            <UncontrolledDropdown nav direction="down">
              <DropdownToggle nav>
                <Avatar.Image
                  size="md"
                  src={randomAvatar()}
                  addOns={[
                    <AvatarAddOn.Icon
                      className="fa fa-circle"
                      color="white"
                      key="avatar-icon-bg"
                    />,
                    <AvatarAddOn.Icon
                      className="fa fa-circle"
                      color="success"
                      key="avatar-icon-fg"
                    />,
                  ]}
                />
              </DropdownToggle>
              <DropdownProfile end userinfo={userInfo} />
            </UncontrolledDropdown>
          </Nav>
        </Box>
      </Navbar>
    </ErrorBoundary>
  )
}

export default GluuNavBar
