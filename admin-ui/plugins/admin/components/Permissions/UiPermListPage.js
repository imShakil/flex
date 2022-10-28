import React, { useEffect, useState, useContext } from 'react'
import MaterialTable from '@material-table/core'
import { Paper } from '@material-ui/core'
import UiPermDetailPage from './UiPermDetailPage'
import { Badge } from 'reactstrap'
import { connect } from 'react-redux'
import { Card, CardBody } from 'Components'
import { useTranslation } from 'react-i18next'
import GluuViewWrapper from 'Routes/Apps/Gluu/GluuViewWrapper'
import applicationStyle from 'Routes/Apps/Gluu/styles/applicationstyle'
import PermissionAddDialogForm from './PermissionAddDialogForm'
import {
  getPermissions,
  deletePermission,
  editPermission,
  addPermission,
} from 'Plugins/admin/redux/actions/ApiPermissionActions'
import {
  hasPermission,
  buildPayload,
  PERMISSION_READ,
  PERMISSION_WRITE,
} from 'Utils/PermChecker'
import SetTitle from 'Utils/SetTitle'
import { ThemeContext } from 'Context/theme/themeContext'
import getThemeColor from 'Context/theme/config'
import useAlert from 'Context/alert/useAlert'

function UiPermListPage({ apiPerms, permissions, loading, dispatch, isSuccess, isError }) {
  const { t } = useTranslation()
  const [modal, setModal] = useState(false)
  const toggle = () => setModal(!modal)
  const myActions = []
  const options = []
  const userAction = {}
  const pageSize = localStorage.getItem('paggingSize') || 10
  const theme = useContext(ThemeContext)
  const { setAlert } = useAlert()

  const selectedTheme = theme.state.theme
  const themeColors = getThemeColor(selectedTheme)
  const bgThemeColor = { background: themeColors.background }
  const alertSeverity = isSuccess ? 'success' : 'error'
  const alertMessage = isSuccess ? t('messages.success_in_saving') : t('messages.error_in_saving')

  useEffect(() => {
    doFetchList()
  }, [])

  useEffect(() => {
    const alertParam = { 
      open: (isSuccess || isError),
      title: isSuccess ? 'Success' : 'Failed',
      text: alertMessage,
      severity: alertSeverity
    }
    setAlert(alertParam)
  }, [isSuccess, isError])

  SetTitle(t('titles.permissions'))

  if (hasPermission(permissions, PERMISSION_WRITE)) {
    myActions.push({
      icon: 'add',
      tooltip: `${t('messages.add_permission')}`,
      iconProps: { color: 'primary' },
      isFreeAction: true,
      onClick: () => handleAddNewPermission(),
    })
  }

  function handleAddNewPermission() {
    toggle()
  }
  function doFetchList() {
    buildPayload(userAction, 'PERMISSIONS', options)
    dispatch(getPermissions(userAction))
  }
  function onAddConfirmed(roleData) {
    buildPayload(userAction, 'message', roleData)
    dispatch(addPermission(userAction))
    toggle()
    doFetchList()
  }
  return (
    <Card style={applicationStyle.mainCard}>
      <CardBody>
        <GluuViewWrapper canShow={hasPermission(permissions, PERMISSION_READ)}>
          <MaterialTable
            components={{
              Container: (props) => <Paper {...props} elevation={0} />,
            }}
            columns={[
              {
                title: `${t('fields.name')}`,
                field: 'permission',
                editable: false,
                width: '50%',
                render: (rowData) => (
                  <Badge color={`primary-${selectedTheme}`}>{rowData.permission}</Badge>
                ),
              },
              { title: `${t('fields.description')}`, field: 'description' },
            ]}
            data={apiPerms}
            isLoading={loading || false}
            title=""
            actions={myActions}
            options={{
              search: true,
              searchFieldAlignment: 'left',
              selection: false,
              pageSize: pageSize,
              rowStyle: (rowData) => ({
                backgroundColor: rowData.enabled ? '#33AE9A' : '#FFF',
              }),
              headerStyle: { ...applicationStyle.tableHeaderStyle, ...bgThemeColor },
              actionsColumnIndex: -1,
            }}
            detailPanel={(rowD) => {
              return <UiPermDetailPage row={rowD} />
            }}
            editable={{
              onRowUpdate: (newData, oldData) =>
                new Promise((resolve, reject) => {
                  buildPayload(userAction, 'Edit permision', newData)
                  dispatch(editPermission(userAction))
                  resolve()
                  doFetchList()
                }),
              onRowDelete: (oldData) =>
                new Promise((resolve, reject) => {
                  buildPayload(userAction, 'Remove permission', oldData)
                  dispatch(deletePermission(userAction))
                  resolve()
                  doFetchList()
                }),
            }}
          />
        </GluuViewWrapper>
        <PermissionAddDialogForm
          handler={toggle}
          modal={modal}
          onAccept={onAddConfirmed}
        />
      </CardBody>
    </Card>
  )
}

const mapStateToProps = (state) => {
  return {
    apiPerms: state.apiPermissionReducer.items,
    loading: state.apiPermissionReducer.loading,
    isSuccess: state.apiPermissionReducer.isSuccess,
    isError: state.apiPermissionReducer.isError,
    permissions: state.authReducer.permissions,
  }
}
export default connect(mapStateToProps)(UiPermListPage)
