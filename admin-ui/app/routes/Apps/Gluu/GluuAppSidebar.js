import React, { useState, useEffect } from 'react'
import { SidebarMenu } from 'Components'
import { connect } from 'react-redux'
import { hasPermission } from 'Utils/PermChecker'
import { ErrorBoundary } from 'react-error-boundary'
import GluuErrorFallBack from './GluuErrorFallBack'
import { processMenus } from 'Plugins/PluginMenuResolver'
import { useTranslation } from 'react-i18next'
import HomeIcon from "Components/SVG/menu/Home"
import AdministratorIcon from "Components/SVG/menu/Administrator"
import OAuthIcon from "Components/SVG/menu/OAuth"
import SchemaIcon from "Components/SVG/menu/Schema"
import ServicesIcon from "Components/SVG/menu/Services"
import UsersIcon from "Components/SVG/menu/Users"

function GluuAppSidebar({ scopes }) {
  const [pluginMenus, setPluginMenus] = useState([])
  const { t } = useTranslation()

  useEffect(() => {
    setPluginMenus(processMenus())
  }, [])

  function getMenuIcon(name) {
    switch (name) {
    case 'admin':
      return <AdministratorIcon className="menu-icon" />

    case 'oauthserver':
      return <OAuthIcon className="menu-icon" />

    case 'services':
      return <ServicesIcon className="menu-icon" />

    case 'schema':
      return <SchemaIcon className="menu-icon" />

    case 'usersmanagement':
      return <UsersIcon className="menu-icon" style={{ top: '-2px' }} />
  
    default:
      return null
    }

  }

  function getMenuPath(menu) {
    if (menu.children) {
      return null
    }
    return menu.path
  }
  function hasChildren(plugin) {
    return typeof plugin.children !== 'undefined' && plugin.children.length
  }

  return (
    <ErrorBoundary FallbackComponent={GluuErrorFallBack}>
      <SidebarMenu>
        {/* -------- Home ---------*/}
        <SidebarMenu.Item
          icon={<HomeIcon className="menu-icon" />}
          title={t('menus.home')}
          textStyle={{ fontSize: '18px' }}
        >
          <SidebarMenu.Item
            title={t('menus.dashboard')}
            to="/home/dashboard"
            textStyle={{ fontSize: '15px', color: '#323b47' }}
            exact
          />
          <SidebarMenu.Item
            title={t('menus.health')}
            to="/home/health"
            textStyle={{ fontSize: '15px' }}
            exact
          />
          <SidebarMenu.Item
            title={t('menus.licenseDetails')}
            to="/home/licenseDetails"
            textStyle={{ fontSize: '15px' }}
            exact
          />
        </SidebarMenu.Item>
        {/* -------- Plugins ---------*/}

        {pluginMenus.map((plugin, key) => (
          <SidebarMenu.Item
            key={key}
            icon={getMenuIcon(plugin.icon)}
            to={getMenuPath(plugin)}
            title={t(`${plugin.title}`)}
            textStyle={{ fontSize: '18px' }}
          >
            {hasChildren(plugin) &&
              plugin.children.map((item, idx) => (
                <SidebarMenu.Item
                  key={idx}
                  title={t(`${item.title}`)}
                  isEmptyNode={
                    !hasPermission(scopes, item.permission) &&
                    !hasChildren(item)
                  }
                  to={getMenuPath(item)}
                  icon={getMenuIcon(item.icon)}
                  textStyle={{ fontSize: '15px' }}
                  exact
                >
                  {hasChildren(item) &&
                    item.children.map((sub, id) => (
                      <SidebarMenu.Item
                        key={id}
                        title={t(`${sub.title}`)}
                        to={getMenuPath(sub)}
                        isEmptyNode={!hasPermission(scopes, sub.permission)}
                        icon={getMenuIcon(sub.icon)}
                        textStyle={{ fontSize: '15px', fontWeight: '400' }}
                        exact
                      ></SidebarMenu.Item>
                    ))}
                </SidebarMenu.Item>
              ))}
          </SidebarMenu.Item>
        ))}

        {/* -------- Plugins ---------*/}
        <SidebarMenu.Item
          icon={<i className="fa fa-fw fa-sign-out mr-2" style={{ fontSize: 28 }}></i>}
          title={t('menus.signout')}
          to="/logout"
          textStyle={{ fontSize: '18px' }}
        />
      </SidebarMenu>
    </ErrorBoundary>
  )
}

const mapStateToProps = ({ authReducer }) => {
  const scopes = authReducer.token
    ? authReducer.token.scopes
    : authReducer.permissions
  return {
    scopes,
  }
}

export default connect(mapStateToProps)(GluuAppSidebar)
