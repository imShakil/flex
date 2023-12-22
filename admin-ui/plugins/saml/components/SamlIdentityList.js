import React, { useCallback, useContext, useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  getSamlIdentites,
  deleteSamlIdentity,
} from 'Plugins/saml/redux/features/SamlSlice'
import MaterialTable from '@material-table/core'
import { useTranslation } from 'react-i18next'
import GluuViewWrapper from 'Routes/Apps/Gluu/GluuViewWrapper'
import { hasPermission, SAML_READ, SAML_WRITE, SAML_DELETE } from 'Utils/PermChecker'
import applicationStyle from 'Routes/Apps/Gluu/styles/applicationstyle'
import { ThemeContext } from 'Context/theme/themeContext'
import getThemeColor from 'Context/theme/config'
import { useNavigate } from 'react-router'
import { DeleteOutlined } from '@mui/icons-material'
import GluuDialog from 'Routes/Apps/Gluu/GluuDialog'
import { buildPayload } from 'Utils/PermChecker'
import { Paper, TablePagination } from '@mui/material'
import GluuAdvancedSearch from 'Routes/Apps/Gluu/GluuAdvancedSearch'

const SamlIdentityList = () => {
  const options = {}
  const theme = useContext(ThemeContext)
  const themeColors = getThemeColor(theme.state.theme)
  const bgThemeColor = { background: themeColors.background }
  const [modal, setModal] = useState(false)
  const [limit, setLimit] = useState(10)
  const [pattern, setPattern] = useState(null)
  const [item, setItem] = useState({})
  const [pageNumber, setPageNumber] = useState(0)

  let memoLimit = limit
  let memoPattern = pattern
  const toggle = () => setModal(!modal)

  const { t } = useTranslation()
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const permissions = useSelector((state) => state.authReducer.permissions)
  const { items, loadingSamlIdp, totalItems } = useSelector(
    (state) => state.idpSamlReducer
  )

  useEffect(() => {
    makeOptions()
    dispatch(getSamlIdentites(options))
  }, [])

  const tableColumns = [
    {
      title: `${t('fields.inum')}`,
      field: 'inum',
    },
    {
      title: `${t('fields.displayName')}`,
      field: 'displayName',
    },
    {
      title: `${t('fields.enabled')}`,
      field: 'enabled',
    },
  ]

  const PaperContainer = useCallback(
    (props) => <Paper {...props} elevation={0} />,
    []
  )

  const handleGoToEditPage = useCallback((rowData, viewOnly) => {
    navigate('/saml/edit', { state: { rowData: rowData, viewOnly: viewOnly } })
  }, [])

  const handleGoToAddPage = useCallback(() => {
    navigate('/saml/add')
  }, [])

  function handleDelete(row) {
    setItem(row)
    toggle()
  }

  function onDeletionConfirmed(message) {
    const userAction = {}
    buildPayload(userAction, message, item.inum)
    dispatch(deleteSamlIdentity({ action: userAction }))
    toggle()
  }

  function makeOptions() {
    setLimit(memoLimit)
    setPattern(memoPattern)
    options['limit'] = memoLimit
    if (memoPattern) {
      options['pattern'] = memoPattern
    }
  }

  const onRowCountChangeClick = (count) => {
    makeOptions()
    options['startIndex'] = 0
    options['limit'] = count
    setPageNumber(0)
    setLimit(count)
    dispatch(getSamlIdentites(options))
  }

  const onPageChangeClick = (page) => {
    makeOptions()
    let startCount = page * limit
    options['startIndex'] = parseInt(startCount)
    options['limit'] = limit
    setPageNumber(page)
    dispatch(getSamlIdentites(options))
  }

  function handleOptionsChange(event) {
    if (event.target.name == 'limit') {
      memoLimit = event.target.value
    } else if (event.target.name == 'pattern') {
      memoPattern = event.target.value
    }
  }

  return (
    <>
      <GluuViewWrapper canShow={hasPermission(permissions, SAML_READ)}>
        <MaterialTable
          key={limit ? limit : 0}
          components={{
            Container: PaperContainer,
            Pagination: (props) => (
              <TablePagination
                count={totalItems}
                page={pageNumber}
                onPageChange={(prop, page) => {
                  onPageChangeClick(page)
                }}
                rowsPerPage={limit}
                onRowsPerPageChange={(prop, count) =>
                  onRowCountChangeClick(count.props.value)
                }
              />
            ),
          }}
          columns={tableColumns}
          data={items}
          isLoading={loadingSamlIdp}
          title=''
          actions={[
            {
              icon: 'edit',
              tooltip: `${t('messages.edit_idp')}`,
              iconProps: { color: 'primary' },
              onClick: (event, rowData) => {
                const data = { ...rowData }
                delete data.tableData
                handleGoToEditPage(data)
              },
              disabled: !hasPermission(permissions, SAML_WRITE),
            },
            {
              icon: 'visibility',
              tooltip: `${t('messages.view_idp_details')}`,
              onClick: (event, rowData) => handleGoToEditPage(rowData, true),
              disabled: !hasPermission(permissions, SAML_READ),
            },
            {
              icon: () => <DeleteOutlined />,
              iconProps: {
                color: 'secondary',
              },
              tooltip: `${t('messages.delete_idp')}`,
              onClick: (event, rowData) => handleDelete(rowData),
              disabled: !hasPermission(permissions, SAML_DELETE),
            },
            {
              icon: () => (
                <GluuAdvancedSearch
                  limitId={'searchLimit'}
                  patternId={'searchPattern'}
                  limit={limit}
                  pattern={pattern}
                  handler={handleOptionsChange}
                  showLimit={false}
                />
              ),
              tooltip: `${t('messages.advanced_search')}`,
              iconProps: { color: 'primary' },
              isFreeAction: true,
              onClick: () => {},
            },
            {
              icon: 'refresh',
              tooltip: `${t('messages.refresh')}`,
              iconProps: { color: 'primary' },
              ['data-testid']: `${t('messages.refresh')}`,
              isFreeAction: true,
              onClick: () => {
                makeOptions()
                dispatch(getSamlIdentites(options))
              },
            },
            {
              icon: 'add',
              tooltip: `${t('messages.add_idp')}`,
              iconProps: { color: 'primary' },
              isFreeAction: true,
              onClick: () => handleGoToAddPage(),
              disabled: !hasPermission(permissions, SAML_WRITE),
            },
          ]}
          options={{
            search: false,
            selection: false,
            pageSize: limit,
            headerStyle: {
              ...applicationStyle.tableHeaderStyle,
              ...bgThemeColor,
            },
            actionsColumnIndex: -1,
          }}
        />
      </GluuViewWrapper>
      {hasPermission(permissions, SAML_DELETE) && (
        <GluuDialog
          row={item}
          name={item?.clientName?.value || ''}
          handler={toggle}
          modal={modal}
          subject='openid connect client'
          onAccept={onDeletionConfirmed}
        />
      )}
    </>
  )
}

export default SamlIdentityList
